Flask-Tasker
==============

Simplify task management in flask applications.

Installation
------------

You can install this package as usual with pip:

    pip install flask-tasker

Example
-------

```python
# python

import time

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from flask_tasker import FlaskTasker


app = Flask(__name__)
CORS(app, origins='*')
socketio = SocketIO(app, cors_allowed_origins="*")
flask_tasker = FlaskTasker(app, socketio)

flags = {}


def preprocessor(task_id, request, on_success, on_error):
    on_success({'count': request.json.get('count')})


@flask_tasker.dispose(preprocessor=preprocessor)
def dispose(task_id, request, on_progress, on_success, on_error, on_terminate):

    flags[task_id] = False

    # Simulate task progress.
    count = request.get('count')

    for i in range(count):
        if flags[task_id]:
            on_terminate()
            return

        # Simulate task error.
        if (round(time.time()) % 10 == 0):
            on_error()
            return
        
        time.sleep(0.5)
        on_progress(data={'progress': (i + 1) / count * 100})

    on_success()


@flask_tasker.terminate()
def terminate(task_id):
    if task_id in flags:
        flags[task_id] = True


if __name__ == '__main__':
    flask_tasker.run('0.0.0.0', 3000, debug=True)
```

Clients are recommended to use [flask-task-client](https://www.npmjs.com/package/flask-tasker-client), because it was developed for this package, it has a more stable API, and it is easier to use.

You can install this package as usual with npm:

    npm install flask-tasker-client

```javascript
// javascript

import {Tasker} from 'flask-tasker-client';

const baseUrl = 'http://localhost:3000';
const tasker = new Tasker({baseUrl});

const dispose = tasker.dispose({
    data: {count: 10},
    onProgress: res => console.log('on progress', res),
    onSuccess: res => console.log('on success', res),
    onError: res => console.error('on error', res),
    onTerminate: res => console.log('on terminate', res)
});
dispose.promise
    .then(res => console.log('on success (promise)', res))
    .catch(err => console.error('on error (promise)', err));

// Simulate task termination.
setTimeout(() => {
    dispose.terminate()
        .then(res => console.log('terminate', res))
        .catch(err => console.error('terminate', err));
}, 1000 * Math.random() * 10);
```

If you want to use the `socket.io-client`, you can use the following code:
```javascript
// javascript

import axios from "axios";
import {io} from "socket.io-client";

const baseUrl = 'http://localhost:3000';
let task_id = '';

io(`${baseUrl}/status`)
   .on('activate', res => {
        console.log('on activate', res);
        task_id = res.task_id;
        axios.post(`${baseUrl}/dispose`, {task_id, count: 10})
            .then(res => console.log('dispose', res.data,))
            .catch(err => console.error('dispose', err));
    })
    .on('progress', res => console.log('on progress', res))
    .on('success', res => console.log('on success', res))
    .on('error', res => console.error('on error', res))
    .on('terminate', res => console.log('on terminate', res));

// Simulate task termination.
setTimeout(() => {
    axios.post(`${baseUrl}/terminate`, {task_id})
        .then(res => console.log('terminate', res.data))
        .catch(err => console.error('terminate', err));
}, 1000 * Math.random() * 10);
```

Resources
---------

- Flask-Tasker
  - [GitHub](https://github.com/xuhuanstudio/flask-tasker)
  - [PyPI](https://pypi.python.org/pypi/Flask-Tasker)
- Flask-Tasker-Client
  - [GitHub](https://github.com/xuhuanstudio/flask-tasker-client)
  - [NPM](https://www.npmjs.com/package/flask-tasker-client)
