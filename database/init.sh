echo "First time running: initializing database from json file"
mongoimport --host localhost --port 27017 -d $MAIN_DB -c $MAIN_COLLECTION --file /tmp/movies.json