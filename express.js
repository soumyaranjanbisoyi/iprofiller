const express = require('express');
const app = express();
const path = require('path');

app.use('/pages/data/public', express.static(path.join(__dirname, 'pages', 'data', 'public')));

app.listen(3000, ()=> {
    console.log("server is running on port 3000")
})