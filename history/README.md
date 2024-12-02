## History service

This Ruby service records user clicks into a RabbitMQ queue

----------------------------------------------------------

Its HTTP interface is:

	POST /record
Records a user's movies preferences on their history
The body of the request must be of MIME type ```application/json```, with this schema:

```ts
	interface Record {
		movieID: string;
		userID: string;
	}
```

The movieID parameter must be a valid movie ID within the system. User IDs are assigned by the frontend service, though they aren't of any particular format. Whether the frontend hands out UUID v4 values as user IDs or uses account IDs or any other method, as long as it can be serialized to a string, it can be used here.

Return value:
```ts
	interface HistoryRequestStatus {
	    status: 'success' | 'failure';
	    error?: string; // reason for the error - set if status == 'failure'
	}
```