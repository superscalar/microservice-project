import vibe.vibe;
import std.stdio;
import std.process;
import std.array;
import std.stdint; // uint16_t type
import std.conv; // to parse strings into ints
import std.container.rbtree; // for a convenient set type
import core.stdc.stdlib; // for exit

MongoClient crossReqClient;
RedBlackTree!(string) crossReqGenreList;
JSONValue jsonGenreList;

void main() {
	string defaultPort = "9191";
	string portAsString = environment.get("MOVIES_SERVICE_PORT", defaultPort);
	uint16_t port = to!uint16_t(portAsString);

	if (port == 0) {
		logInfo("Don't pick port 0 -> The OS will pick any available port, but the other services won't know it");
		exit(-1);
	}
	
	// For local testing, don't pass "localhost" in - it defaults to IPv6 ::1, which the mongodb instance doesn't listen on
	// 127.0.0.1 forces IPv4
	string MONGODB_URL = environment.get("MONGODB_URL", "127.0.0.1");
	logInfo("Connecting to " ~ MONGODB_URL);
	MongoClient client = connectMongoDB(MONGODB_URL);
	crossReqClient = client;

	auto settings = new HTTPServerSettings;
	settings.port = port;
	settings.bindAddresses = ["0.0.0.0", "::"];

	auto router = new URLRouter;
	router.get("/getMovieById/:movieID", &getMovieById);
	router.get("/getSampleByGenre", &getSampleByGenre);
	router.get("/getGenreList", &getGenreList);
	auto listener = listenHTTP(settings, router);

	auto genreList = getGenreListFromDB();
	writeln("[DEBUG] Genres from the database: ", genreList);
	crossReqGenreList = genreList;
	
	string[] genreArray = array(genreList[]);
	jsonGenreList = JSONValue( genreArray );

	scope (exit) {
		listener.stopListening();
	}

	logInfo("Now running on port " ~ to!string(settings.port));
	runApplication();
}

// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

RedBlackTree!(string) getGenreListFromDB() {
	// The default red black tree implementation in the stdlib doesn't allow duplicates. It behaves like a set.
	RedBlackTree!(string) genreSet = redBlackTree!(string);

	MongoCollection collection = crossReqClient.getCollection("peliculas.movies");
	auto movieGenres = collection.find(Bson.emptyObject, ["_id": 0, "genres": 1]);
	foreach(g; movieGenres) {
		Bson genresForMovie = g["genres"];
		if (!genresForMovie.isNull()) {
			string[] genresArray = deserializeBson!(string[])(genresForMovie);
			// writeln(genresArray);
			genreSet.insert(genresArray);
		}
	}

	return genreSet;
}

import std.json;
void getGenreList(HTTPServerRequest req, HTTPServerResponse res) {
	res.contentType = "application/json; charset=UTF-8";
	
	res.writeBody( jsonGenreList.toString() );
}

int tryParseInt(string str, int default_value) {
	try {
		int n = to!int(str);
		return n;
	} catch (std.conv.ConvException ex) {
		return default_value;
	}
}

void getSampleByGenre(HTTPServerRequest req, HTTPServerResponse res) {
	res.contentType = "application/json; charset=UTF-8";

	auto queryParams = req.query;
	string genre;
	int n;
	int defaultN = 20;

	if ("genre" in queryParams) {
		genre = queryParams["genre"];
	} else {
		genre = "Fantasy";
	}

	if ("n" in queryParams) {
		n = tryParseInt( queryParams["n"], defaultN );
	} else {
		n = defaultN;
	}

	if (genre in crossReqGenreList) {
		MongoCollection collection = crossReqClient.getCollection("peliculas.movies");
		// https://vibed.org/api/vibe.db.mongo.collection/MongoCollection.aggregate ---> sample
		Bson sample = collection.aggregate(
			["$match": ["genres": ["$in": [ genre ] ] ] ],
			["$sample": ["size": n]]
		);

		Json sampleAsJson = sample.toJson();

		// replace _id with id
		foreach (j; sampleAsJson) {
			auto id = j["_id"];
			j.remove("_id");
			j["id"] = id;
		}

		res.writeBody( sampleAsJson.toString() );
	} else {
		// if no genre or an invalid genre is given, I pick a default genre, but another possibility is to error out
		// Either way is fine, but picking a default genre returns movies even for a plain "GET /getSampleByGenre"
		res.writeBody("{\"error\": \"Invalid genre: " ~ genre ~"\"}");
	}
}

// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

void getMovieById(HTTPServerRequest req, HTTPServerResponse res) {
	MongoCollection collection = crossReqClient.getCollection("peliculas.movies");

	string movieID = req.params["movieID"];
	BsonObjectID oid;
	oid = oid.fromString(movieID);

	Bson movie = collection.findOne(["_id": oid]);

	// remove ObjectId and replace _id with id to return to the rest of the system
	Bson id = movie["_id"];
	movie.remove("_id");
	string idString = id.toString();
	movie["id"] = idString[9..idString.length-1];

	res.contentType = "application/json; charset=UTF-8";
	res.writeBody(movie.toString());
}
