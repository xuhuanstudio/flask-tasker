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

from flask import Flask
from flask_tasker import FlaskTasker
from flask_cors import CORS
from flask_socketio import SocketIO


app = Flask(__name__)
CORS(app, origins='*')
socketio = SocketIO(app, cors_allowed_origins="*")
flask_tasker = FlaskTasker(app, socketio)

flags = {}


@flask_tasker.dispose()
def dispose(task_id, request, on_progress, on_success, on_error, on_terminate):

    flags[task_id] = False

    # Simulate task progress.
    import time
    count = request.json.get('count')

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

```javascript
// javascript

import axios from "axios";
import {io} from "socket.io-client";

const rootUrl = 'http://localhost:3000';

axios.post(`${rootUrl}/dispose`, {count: 10}).then(res => {

    const task_id = res.data.task_id;
    console.log('task_id', task_id);

    io(`${rootUrl}/status`, {query: {task_id}})
        .on('success', res => console.log('on success', res))
        .on('error', res => console.error('on error', res))
        .on('terminate', res => console.log('on terminate', res))
        .on('progress', res => {
            console.log('on progress', res);
            // Simulate task termination.
            if (Math.random() < 0.08) {
                axios.post(`${rootUrl}/terminate`, {task_id})
                    .then(res => console.log('terminate', res.data))
                    .catch(console.error);
            }
        });
    
}).catch(console.error);
```

Resources
---------

- [GitHub](https://github.com/xuhuanstudio/flask-tasker)
- [PyPI](https://pypi.python.org/pypi/Flask-Tasker)
