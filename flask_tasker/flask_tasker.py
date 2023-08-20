import copy
import uuid
import threading

from flask import request
from flask_socketio import join_room, leave_room


class FlaskTasker():
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio
        self.task_queue = {}


    def dispose(self, rule='/dispose', namespace='/status', methods=['POST'], use_lock=True):
        """
        dispose task
        """

        @self.socketio.on('connect', namespace=namespace)
        def connect():
            task_id = request.args.get('task_id')
            if task_id not in self.task_queue:
                self.task_queue[task_id] = []
            self.task_queue[task_id].append(request.sid)
            join_room(task_id, namespace=namespace)

        @self.socketio.on('disconnect', namespace=namespace)
        def disconnect():
            sid = request.sid
            task_id = request.args.get('task_id')
            if task_id in self.task_queue and sid in self.task_queue[task_id]:
                self.task_queue[task_id].remove(sid)
                leave_room(task_id, namespace=namespace)
        
        def decorator(func):

            @self.app.route(rule, methods=methods)
            def task_dispose_route():
                _request = copy.copy(request)
                task_id = str(uuid.uuid4())
                base_data = {'task_id': task_id}
                task_lock = threading.Lock() if use_lock else None
                result = None

                def on_progress(data=base_data, event='progress'):
                    self.socketio.emit(event, data, room=task_id, namespace=namespace)

                def on_complete(data=base_data, event='complete'):
                    if task_id in self.task_queue:
                        self.socketio.emit(event, data, room=task_id, namespace=namespace)
                        del self.task_queue[task_id]

                def on_success(data=base_data, event='success'):
                    on_complete(data, event)

                def on_error(data=base_data, event='error'):
                    on_complete(data, event)

                def on_terminate(data=base_data, event='terminate'):
                    on_complete(data, event)

                def thread_target():
                    if task_lock is None:
                        result = func(task_id, _request, on_progress, on_success, on_error, on_terminate)
                    else:
                        with task_lock:
                            result = func(task_id, _request, on_progress, on_success, on_error, on_terminate)
                            
                threading.Thread(target=thread_target).start()
                return result if result is not None else base_data
            
        return decorator
    

    def terminate(self, rule='/terminate', namespace='/status', methods=['POST'], event='terminate'):
        """
        terminate task
        """
        def decorator(func):

            @self.app.route(rule, methods=methods)
            def task_terminate_route():
                task_id = request.json.get('task_id', request.form.get('task_id', request.args.get('task_id')))
                result = func(task_id)
                return result if result is not None else {'task_id': task_id}
            
        return decorator
    

    def run(self, host=None, port=None, **kwargs):
        """
        start the server
        """
        self.socketio.run(self.app, host=host, port=port, **kwargs)


    def stop(self):
        """
        stop the server
        """
        self.socketio.stop()
