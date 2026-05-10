const express = require("express");
const jwt = require("jsonwebtoken");

const app = express();
app.use(express.json());

const JWT_SECRET = "development-secret";

app.post("/login", (req, res) => {
  const username = req.body.username;
  const token = jwt.sign({ sub: username }, JWT_SECRET);
  res.json({ token });
});

app.get("/users/:id", async (req, res) => {
  const sql = `SELECT * FROM users WHERE id = ${req.params.id}`;
  res.json({ sql });
});

app.listen(3000);
