(ql:quickload :hunchentoot)
(ql:quickload :uiop)
(ql:quickload :dexador)
(ql:quickload :jonathan)
(ql:quickload :simple-routes)
(ql:quickload :uuid)

(defvar *file-root* #P".") ; file root for the web server to look for files

(defun get-or-fail (var) (if (eq NIL (uiop:getenv var)) (progn (format t "Missing environment variable ~A !" var) (exit)) (uiop:getenv var) ))

(defvar FRONTEND_PORT (parse-integer (get-or-fail "FRONTEND_PORT")) )
(defvar FRONTEND_SECRET (get-or-fail "FRONTEND_SECRET"))
(defvar RANDOM_MOVIES_SERVICE (get-or-fail "RANDOM_MOVIES_SERVICE"))
(defvar HISTORY_SERVICE_URL (get-or-fail "HISTORY_SERVICE_URL"))
(defvar HISTORY_SERVICE_NAME (get-or-fail "HISTORY_SERVICE_NAME"))
(defvar RECOMMENDER_SERVICE_URL (get-or-fail "RECOMMENDER_SERVICE_URL"))
(defvar MOVIES_SERVICE (get-or-fail "MOVIES_SERVICE"))
(defvar HISTORY_PORT (get-or-fail "HISTORY_PORT"))

(defun root-handler ()
	; calling session-value without a session initializes one
	; we only want to give the user a new ID if they don't already have one
	(if (eq NIL (hunchentoot:session-value :userID))
		(setf (hunchentoot:session-value :userID) (format nil "~S" (uuid:make-v4-uuid)) )
		()
	)

	(setf (hunchentoot:content-type*) "text/html")
	(format t "[DEBUG] ~A" (hunchentoot:session-value :userID))
	(uiop:read-file-string "index.html")
)

(defun random-movies-handler ()
	(setf (hunchentoot:content-type*) "application/json")
	(let (
			(randomMoviesURL (format nil "~A/randomMovies" RANDOM_MOVIES_SERVICE))
		)
	; in
		(multiple-value-bind
				(content #|status headers-hash-table|#)
				(dex:get randomMoviesURL)
			content
		)
	)
)

(defun get-movie-by-id-handler (id)
	; (format t "~A~%" (hunchentoot:session-value :userID))
	(setf (hunchentoot:content-type*) "application/json")
	(let (
			(movie-by-id-endpoint (format nil "~A/getMovieById/~A" MOVIES_SERVICE id))
		)
	; in
		(multiple-value-bind
				(content #|status headers-hash-table|#)
				(dex:get movie-by-id-endpoint)
			content
		)
	)
)

(defun history-handler ()
	(setf (hunchentoot:content-type*) "application/json")
	(let (
			(user-id (hunchentoot:session-value :userID))
			(json-post-body (jonathan:parse (hunchentoot:raw-post-data :force-text t) :as :hash-table))
			(history-endpoint (format nil "~A/history" HISTORY_SERVICE_URL))
		)
	; in
		; add the session's user id and pass on the record to the history service
		(setf (gethash "userID" json-post-body) user-id)

		; POST to the service and return the status code
		(multiple-value-bind
				(content #|status headers-hash-table|#)
				(dex:post history-endpoint
						:content (jonathan:to-json json-post-body)
						:headers '( ("Content-Type" . "application/json") )
				)
			content
		)
	)
)

(defun recommend-handler ()
	(setf (hunchentoot:content-type*) "application/json")
	(let* (
			(user-id (hunchentoot:session-value :userID))
			(recommender-endpoint (format nil "~A/getRecommendation/~A" RECOMMENDER_SERVICE_URL user-id))
		)
	; in
		(multiple-value-bind
				(content #|status headers-hash-table|#)
				(dex:get recommender-endpoint)
			content
		)
	)
)

(setf hunchentoot:*session-secret* FRONTEND_SECRET)

(setf simple-routes:*routeslist*
    (simple-routes:compile-routes
       (:GET  ""                   'root-handler)
       (:GET  "/"                  'root-handler)
       (:GET  "/randomMovies"      'random-movies-handler)
       (:GET  "/getMovieById/:id"  'get-movie-by-id-handler)
       (:GET  "/recommend"         'recommend-handler)
       (:POST "/history"           'history-handler)
    )
)

(defvar *server* (make-instance 'simple-routes:simpleroutes-acceptor
					  :address "0.0.0.0" :port FRONTEND_PORT
					  :document-root *file-root*
					  :access-log-destination *terminal-io*
					  :message-log-destination *terminal-io*))					  

(hunchentoot:start *server*)
(format t "*---------------------------------------------*~%"              )
(format t "*------> Now listening on 0.0.0.0:~D <------*~%"   FRONTEND_PORT)
(format t "*---------------------------------------------*~%"              )