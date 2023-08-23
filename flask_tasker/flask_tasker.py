import inspect
from typing import Any, Callable
import uuid
import threading

from flask import request
from flask_socketio import join_room, leave_room, emit

from .flask_request import FlaskRequest


class FlaskTasker():
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio
        self.task_queue = {}
    

    def dispose(self, rule='/dispose', namespace='/status', methods=['POST'], use_lock=True, preprocessor=None):
        """
        Dispose task decorator

        Args:
            - rule (str, optional): The rule of the route. Defaults to '/dispose'.
            - namespace (str, optional): The namespace of the socketio. Defaults to '/status'.
            - methods (list, optional): The methods of the route. Defaults to ['POST'].
            - use_lock (bool, optional): Whether to use lock. Defaults to True.
            - preprocessor (Callable, optional): The function to preprocess the request. Defaults to None.

        Decorator Args:
            - task_id (str, optional): The task id.
            - request (FlaskRequest, optional): If preprocessor is None, request is FlaskRequest. Otherwise, request is the result of preprocessor.
            - on_progress (Callable[[any], None], optional): The function to send progress.
            - on_success (Callable[[any], None], optional): The function to send success.
            - on_error (Callable[[any], None], optional): The function to send error.
            - on_terminate (Callable[[any], None], optional): The function to send terminate.
        """
        def decorator(func: Callable[
            [
                str, Any, 
                Callable[[any, str], None], 
                Callable[[any, str], None], 
                Callable[[any, str], None], 
                Callable[[any, str], None]],
            None
        ]):

            @self.socketio.on('connect', namespace=namespace)
            def connect():
                task_id = request.args.get('task_id')

                if task_id == None:
                    task_id = str(uuid.uuid4())
                    self.task_queue[task_id] = []
                    self.task_queue[task_id].append(request.sid)
                    join_room(task_id, namespace=namespace)
                    emit('activate', {'task_id': task_id})
                else:
                    if task_id not in self.task_queue:
                        emit('error', {'task_id': task_id, 'error': 'task not found'})
                        return
                    else:
                        self.task_queue[task_id].append(request.sid)
                        join_room(task_id, namespace=namespace)


            @self.socketio.on('disconnect', namespace=namespace)
            def disconnect():
                sid = request.sid
                task_id = request.args.get('task_id')
                if task_id in self.task_queue and sid in self.task_queue[task_id]:
                    self.task_queue[task_id].remove(sid)
                    leave_room(task_id, namespace=namespace)


            @self.app.route(rule, methods=methods)
            def task_dispose_route():
                _request = FlaskRequest(request)
                task_id = _request.json.get('task_id', _request.form.get('task_id', _request.args.get('task_id')))
                
                if task_id not in self.task_queue:
                    return {'task_id': task_id, 'data': 'task not found'}, 404
                
                task_lock = threading.Lock() if use_lock else None

                def package_data(data=None):
                    if data is None:
                        return {'task_id': task_id}
                    # elif isinstance(data, dict):
                    #     return {'task_id': task_id, **data}
                    return {'task_id': task_id, 'data': data}

                def on_progress(data=None, event='progress'):
                    self.socketio.emit(event, package_data(data), room=task_id, namespace=namespace)

                def on_complete(data=None, event='complete'):
                    if task_id in self.task_queue:
                        self.socketio.emit(event, package_data(data), room=task_id, namespace=namespace)
                        del self.task_queue[task_id]

                def on_success(data=None, event='success'):
                    on_complete(data, event)

                def on_error(data=None, event='error'):
                    on_complete(data, event)

                def on_terminate(data=None, event='terminate'):
                    on_complete(data, event)

                def thread_target(data):
                    parameters_len = len(inspect.signature(func).parameters)
                    args = [task_id, data, on_progress, on_success, on_error, on_terminate][:parameters_len]

                    if task_lock is None:
                        func(*args)
                        return
                    
                    with task_lock:
                        func(*args)

                def on_preprocess_success(data=_request):
                    if preprocess_result['is_preprocess_success'] != None:
                        raise Exception('Preprocessor callback has been called')
                    preprocess_result['is_preprocess_success'] = True
                    threading.Thread(target=thread_target, args=(data,)).start()

                def on_preprocess_error(data='Preprocessor error'):
                    if preprocess_result['is_preprocess_success'] != None:
                        raise Exception('Preprocessor callback has been called')
                    preprocess_result['is_preprocess_success'] = False
                    preprocess_result['data'] = data
                    on_error(data)

                if preprocessor == None:
                    threading.Thread(target=thread_target, args=(_request,)).start()
                    return package_data(), 200
                
                preprocess_result = {
                    'is_preprocess_success': None,
                    'data': None
                }
                preprocessor(task_id, _request, on_preprocess_success, on_preprocess_error)

                if preprocess_result['is_preprocess_success'] == None:
                    threading.Thread(target=thread_target, args=(_request,)).start()
                    return package_data(), 200
                return package_data(preprocess_result['data']), 200 if preprocess_result['is_preprocess_success'] else 500
                
                
        return decorator
    

    def terminate(self, rule='/terminate', namespace='/status', methods=['POST'], event='terminate'):
        """
        Terminate task decorator

        Args:
            - rule (str, optional): The rule of the route. Defaults to '/terminate'.
            - namespace (str, optional): The namespace of the socketio. Defaults to '/status'.
            - methods (list, optional): The methods of the route. Defaults to ['POST'].
            - event (str, optional): The event to be emitted. Defaults to 'terminate'.

        Decorator Args:
            - task_id (str): The task id.
        """
        def decorator(func: Callable[[str], None]):

            @self.app.route(rule, methods=methods)
            def task_terminate_route():
                task_id = request.json.get('task_id', request.form.get('task_id', request.args.get('task_id')))
                if task_id not in self.task_queue:
                    return {'task_id': task_id, 'data': 'task not found or task has been terminated'}, 404
                
                result = func(task_id)
                if result is None:
                    return {'task_id': task_id}, 200

                if isinstance(result, tuple):
                    res, data = result
                    if res:
                        return {'task_id': task_id, 'data': data}, 200
                    return {'task_id': task_id, 'data': data}, 500

                if result:
                    return {'task_id': task_id}, 200
                return {'task_id': task_id}, 500
            
        return decorator
    

    def run(self, host=None, port=None, **kwargs):
        """
        Start the server

        Args:
            This method has the same arguments as socketio.run method, 
            except that it does not require the app argument.
        """
        self.socketio.run(self.app, host=host, port=port, **kwargs)


    def stop(self):
        """
        Stop the server
        """
        self.socketio.stop()
