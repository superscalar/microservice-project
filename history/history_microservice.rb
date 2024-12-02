require 'sinatra'
require 'sinatra/cors'
require 'bunny'
require 'json'

set :bind, '0.0.0.0'
disable :protection
set :allow_origin, "*"

amqp_URL = ENV["MESSAGE_QUEUE_URL"] || raise("MESSAGE_QUEUE_URL required!")

conn = Bunny.new amqp_URL
conn.start
channel = conn.create_channel
queue = channel.queue("history", durable: true)

get "/" do
	return '<marquee scrollamount=15 style="max-width: 500px; font-family: Verdana, sans; font-size: 1.5rem;"> .:: History Microservice :: History Microservice :: History Microservice :: History Microservice ::.</marquee>'
end

# to test:
# curl -X POST "http://localhost:4567/history" -H "Content-Type: application/json" -d '{"userID": "USERID", "movieID": "MOVIEID"}'
post "/history" do
	content_type :json

	record = JSON.parse(request.body.read)
	isInvalidRecord = record['userID'].nil? or record['movieID'].nil?
	return {"status" => "failure",
			"error" => "Wrong parameters (missing userID or movieID)"
		}.to_json if isInvalidRecord

	historyRecord = JSON.generate({ "userID" => record['userID'], 'movieID' => record['movieID'] })

	puts " [DEBUG] Sending #{historyRecord} to the queue"
	channel.default_exchange.publish(historyRecord, routing_key: queue.name, persistent: true)
	return {"status" => "success"}.to_json
end