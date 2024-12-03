#[macro_use] extern crate rocket;
use std::env;
use reqwest;

const SAMPLE_BY_GENRE_ENDPOINT: &str = "/getSampleByGenre";
const GENRES_ENDPOINT: &str = "/getGenreList";

// fn print_type_of<T>(_: &T) { println!("{}", std::any::type_name::<T>()); }

use rocket::http::Header;
use rocket::{Request, Response};
use rocket::fairing::{Fairing, Info, Kind};
pub struct CORS;
#[rocket::async_trait]
impl Fairing for CORS {
    fn info(&self) -> Info {
        Info {
            name: "Add CORS headers to responses",
            kind: Kind::Response
        }
    }

    async fn on_response<'r>(&self, _request: &'r Request<'_>, response: &mut Response<'r>) {
        response.set_header(Header::new("Access-Control-Allow-Origin", "*"));
        response.set_header(Header::new("Access-Control-Allow-Methods", "POST, GET, PATCH, OPTIONS"));
        response.set_header(Header::new("Access-Control-Allow-Headers", "*"));
        response.set_header(Header::new("Access-Control-Allow-Credentials", "true"));
    }
}

// https://api.rocket.rs/v0.4/rocket/struct.State
use rocket::State;
struct RocketState {
    movies_service: String,
    genre_list: Vec<String>
}

async fn get_genre_list(movies_service: String) -> RocketState {
    let genres_endpoint = movies_service.clone() + GENRES_ENDPOINT;
    match reqwest::Client::new().get(genres_endpoint).send().await {
        Ok(response) => {
            let body = response.text().await.unwrap();
            match serde_json::from_str::<Vec<String>>(&body) {
                Ok(parsed_body) => RocketState { movies_service: movies_service, genre_list: parsed_body },
                Err(e) => {
                    println!("Error @ get_genre_list: {:?}", e);

                    // This return value is just to make the function simpler. It should really return Result<Vec<String>> for genre_list
                    RocketState { movies_service: movies_service, genre_list: vec!["Fantasy".to_string()] }
                },
            }
        },

        // This return value is just to make the function simpler. It should really return Result<Vec<String>> for genre_list
        Err(_) => RocketState { movies_service: movies_service, genre_list: vec!["Adventure".to_string()] }
    }
    
}

use rand::Rng;
fn random_genre_query_url(movies_service: &String, genre_list: &Vec<String>) -> String {
    let mut rng = rand::thread_rng();
    let n_movies = rng.gen_range(20..30);
    let genre = &genre_list[rng.gen_range(0..genre_list.len())]; // pick a random genre
    format!("{}{}?genre={}&n={}", movies_service, SAMPLE_BY_GENRE_ENDPOINT, genre, n_movies)
}

use rocket::http::ContentType;
#[get("/randomMovies")]
async fn recommend(state: &State<RocketState>) -> (ContentType, String) {
    // Get a random sample of a randomly picked genre from the movies service, and forward it to whoever asks
    match reqwest::Client::new().get( random_genre_query_url(&state.movies_service, &state.genre_list) ).send().await {
        Ok(response) => {
            let body = response.text().await.unwrap();
            (ContentType::JSON, body)
        },
        Err(_) => (ContentType::HTML, String::from(""))
    }
}

#[rocket::main]
async fn main() {
    let movies_service = match env::var("MOVIES_SERVICE") {
        Ok(url) => url,
        Err(_e) => { std::panic!("Please provide a MOVIES_SERVICE environment variable with a valid URL"); }
    };

    let port = match env::var("RANDOM_MOVIES_PORT") {
        Ok(port) => port.parse::<u16>().unwrap(),
        Err(_e) => { std::panic!("Please provide a RANDOM_MOVIES_PORT environment variable with a valid integer between 1 and 65535"); }
    };

    if port == 0 {
        std::panic!("Don't pick port 0 -> The OS will pick any available port, but the other services won't know it")
    }

    let config = rocket::Config::figment()
                    .merge( ("port", port) )
                    .merge(("address", "0.0.0.0"));

    let per_request_state: RocketState = get_genre_list(movies_service).await;
    println!("[DEBUG] Got {:?} from {:?}", per_request_state.genre_list, GENRES_ENDPOINT);

    let _ = rocket::build()
        .configure(config)
        .mount("/", routes![recommend])
        .manage(per_request_state)
        .launch()
        .await;
}