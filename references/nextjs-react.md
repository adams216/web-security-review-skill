# Next.js & React Security Reference

## Next.js Specific Checks

### Server Actions & API Routes
- Validate and sanitize all inputs in `app/api/*` and `actions/*.ts`
- Never trust `req.headers` for auth without verification
- Check that server actions re-validate session server-side (don't rely only on middleware)
- Ensure `revalidatePath` / `revalidateTag` are not callable by unauthenticated users

### Environment Variables
- `NEXT_PUBLIC_*` vars are exposed to the browser — never put secrets there
- Verify `.env.local` is in `.gitignore`
- Check for accidental secret exposure in client components

### dangerouslySetInnerHTML
```jsx
// ❌ VULNERABLE — XSS
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// ✅ FIXED — sanitize first
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userInput) }} />
```

### next.config.js Security Headers
Always check for a `headers()` export:
```js
// ✅ Recommended headers config
async headers() {
  return [{
    source: '/(.*)',
    headers: [
      { key: 'X-Frame-Options', value: 'DENY' },
      { key: 'X-Content-Type-Options', value: 'nosniff' },
      { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
      { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
      {
        key: 'Content-Security-Policy',
        value: "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
      }
    ]
  }];
}
```

### Authentication (NextAuth / Auth.js)
- Check `callbacks.session` doesn't expose sensitive user fields
- Ensure `NEXTAUTH_SECRET` is set and strong
- Verify protected routes are guarded in both middleware AND server components
- Check for JWT secret rotation strategy

### SSRF via fetch()
```js
// ❌ VULNERABLE — user controls URL
const data = await fetch(req.query.url);

// ✅ FIXED — whitelist allowed domains
const ALLOWED = ['https://api.example.com'];
if (!ALLOWED.some(a => url.startsWith(a))) throw new Error('Forbidden');
const data = await fetch(url);
```

---

## React Specific Checks

### State & Props
- Never store sensitive data (tokens, passwords) in component state or Redux store without encryption
- Avoid logging props that may contain PII

### Third-party Components
- Audit npm packages that render HTML (rich text editors, markdown renderers)
- Check for prototype pollution in utility libraries

### Client-side Auth Checks
- Never rely solely on client-side route guards — always enforce on the server
- `localStorage` tokens are XSS-vulnerable; prefer `HttpOnly` cookies

### Common Vulnerable Patterns
```jsx
// ❌ Reflected XSS via URL param
const { searchParams } = new URL(window.location.href);
document.getElementById('out').innerHTML = searchParams.get('q');

// ✅ Use textContent instead
document.getElementById('out').textContent = searchParams.get('q');
```
