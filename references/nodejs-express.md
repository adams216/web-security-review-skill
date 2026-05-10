# Node.js & Express Security Reference

## Must-Have Middleware

```js
const helmet = require('helmet');         // security headers
const rateLimit = require('express-rate-limit');
const mongoSanitize = require('express-mongo-sanitize');
const xss = require('xss-clean');
const hpp = require('hpp');               // HTTP param pollution

app.use(helmet());
app.use(mongoSanitize());
app.use(xss());
app.use(hpp());

const limiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 100 });
app.use('/api', limiter);
```

Flag any Express app missing `helmet` as 🟡 Medium.
Flag missing rate limiting on auth routes as 🟠 High.

## SQL / NoSQL Injection

```js
// ❌ VULNERABLE — string interpolation in query
db.query(`SELECT * FROM users WHERE id = ${req.params.id}`);

// ✅ FIXED — parameterized
db.query('SELECT * FROM users WHERE id = ?', [req.params.id]);

// ❌ VULNERABLE — MongoDB operator injection
User.find({ username: req.body.username }); // attacker sends { $gt: '' }

// ✅ FIXED — sanitize or validate type
if (typeof req.body.username !== 'string') return res.status(400).end();
User.find({ username: req.body.username });
```

## JWT Security

```js
// ❌ Weak: algorithm confusion attack possible
jwt.verify(token, secret); // doesn't pin algorithm

// ✅ Fixed: always pin the algorithm
jwt.verify(token, secret, { algorithms: ['HS256'] });

// ❌ Secret too short or hardcoded
const JWT_SECRET = 'secret';

// ✅ Long random secret from environment
const JWT_SECRET = process.env.JWT_SECRET; // min 32 chars, random
```

Flags:
- `alg: 'none'` accepted → 🔴 Critical
- JWT secret < 32 chars → 🟠 High
- Token not expiring (`expiresIn` missing) → 🟡 Medium

## File Upload Security

```js
// ❌ VULNERABLE — no validation
app.post('/upload', upload.single('file'), (req, res) => {
  // saves anything including .php, .exe, .sh
});

// ✅ FIXED
const upload = multer({
  limits: { fileSize: 5 * 1024 * 1024 }, // 5MB max
  fileFilter: (req, file, cb) => {
    const allowed = ['image/jpeg', 'image/png', 'application/pdf'];
    cb(null, allowed.includes(file.mimetype));
  }
});
```

## CORS Configuration

```js
// ❌ VULNERABLE — open to any origin
app.use(cors());

// ✅ FIXED — whitelist specific origins
app.use(cors({
  origin: ['https://myapp.com', 'https://www.myapp.com'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
}));
```

## Error Handling

```js
// ❌ Exposes stack traces to client
app.use((err, req, res, next) => {
  res.status(500).json({ error: err.stack });
});

// ✅ Log internally, generic message externally
app.use((err, req, res, next) => {
  console.error(err); // or your logger
  res.status(500).json({ error: 'Something went wrong' });
});
```

## GraphQL Security

```js
// ❌ VULNERABLE — no depth or complexity limit
const server = new ApolloServer({ schema });

// ✅ FIXED
import depthLimit from 'graphql-depth-limit';
import { createComplexityLimitRule } from 'graphql-validation-complexity';

const server = new ApolloServer({
  schema,
  validationRules: [
    depthLimit(7),
    createComplexityLimitRule(1000),
  ],
  introspection: process.env.NODE_ENV !== 'production', // disable in prod
});
```

Flag: introspection enabled in production → 🟡 Medium (leaks schema to attackers)
Flag: no query depth limit → 🟠 High (DoS via deeply nested queries)

## WebSocket Security

```js
// ❌ VULNERABLE — no origin check
const wss = new WebSocket.Server({ port: 8080 });

// ✅ FIXED — validate origin on upgrade
const wss = new WebSocket.Server({
  port: 8080,
  verifyClient: ({ origin, req }, cb) => {
    const allowed = ['https://myapp.com'];
    cb(allowed.includes(origin), 403, 'Forbidden');
  }
});
```

Also check: WebSocket messages are authenticated per-message, not just on connect.

## Prototype Pollution (CWE-1321)

```js
// ❌ VULNERABLE — deep merge without sanitization
function merge(target, source) {
  for (let key in source) target[key] = source[key]; // __proto__ attack
}

// ✅ FIXED — use safe merge
const _ = require('lodash');
_.mergeWith(target, source, (obj, src, key) => {
  if (key === '__proto__' || key === 'constructor') return obj;
});
// Or use: Object.assign({}, source) for shallow merge
```

## Environment & Secrets

- Check `dotenv` is loaded before any config
- Verify `.env` is in `.gitignore`
- Flag any secret in source code as 🔴 Critical
- Check `NODE_ENV=production` disables debug features
- Scan git history: `git log -p | grep -E "(password|secret|api_key|token)" -i`
