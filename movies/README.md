## Movies Service

This microservice, written in D, has the following HTTP interface:

----------------------------------------------------------

    GET /getMovieById/:movieID
Pass in a valid movie ID as a parameter.
Example: ```/getMovieById/573a13b8f29313caabd4b3c0```
Returns: That movie's details. MIME type: ```application/json```

----------------------------------------------------------
	GET /getSampleByGenre?genre=<GENRE>?n=<N>
Returns a sample of ```n``` movies of genre ```GENRE``` from the set of all movies.
Parameters:
* genre: a valid genre for a movie. You can get the list of all available genres with /getGenreList. Default value: "Fantasy"
* n: a positive integer. Default value: 20

----------------------------------------------------------

	GET /getGenreList
Returns a JSON array of strings, comprising all the genres available to ask for at ```/getSampleByGenre```