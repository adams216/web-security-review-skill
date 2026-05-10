# WordPress & PHP Security Reference

## WordPress Security Checklist

### Core Hardening
- [ ] WordPress core, themes, and plugins are up to date
- [ ] Default `admin` username has been changed
- [ ] `wp-config.php` is outside the web root (or protected)
- [ ] File editing via dashboard is disabled: `define('DISALLOW_FILE_EDIT', true);`
- [ ] XML-RPC is disabled if not needed
- [ ] Directory listing disabled in `.htaccess`
- [ ] `readme.html` and `license.txt` removed (version disclosure)

### wp-config.php Audit
```php
// ✅ Required security keys (check they're set and not default)
define('AUTH_KEY',         'unique-random-string');
define('SECURE_AUTH_KEY',  'unique-random-string');
// ... (all 8 keys)

// ✅ Limit DB user privileges — should NOT be root
define('DB_USER', 'wp_limited_user');

// ✅ Disable debug in production
define('WP_DEBUG', false);
define('WP_DEBUG_LOG', false);
define('WP_DEBUG_DISPLAY', false);

// ✅ Force SSL
define('FORCE_SSL_ADMIN', true);
```

### Plugin Vulnerability Scan
Check installed plugins against the WPScan database. Key risk factors:
- Plugins not updated in 2+ years
- Plugins with < 1000 active installs from unknown authors
- Known CVEs: check https://wpscan.com/plugins

Common vulnerable plugin categories: page builders, form plugins, SEO plugins, file managers.

### .htaccess Security Rules
```apache
# Protect wp-config.php
<files wp-config.php>
  order allow,deny
  deny from all
</files>

# Disable directory browsing
Options -Indexes

# Block access to sensitive files
<FilesMatch "\.(log|sql|bak|env)$">
  Order Allow,Deny
  Deny from all
</FilesMatch>
```

---

## PHP Security Checks

### SQL Injection
```php
// ❌ VULNERABLE
$result = mysqli_query($conn, "SELECT * FROM users WHERE id = " . $_GET['id']);

// ✅ FIXED — prepared statements
$stmt = $conn->prepare("SELECT * FROM users WHERE id = ?");
$stmt->bind_param("i", $_GET['id']);
$stmt->execute();
```

### XSS Prevention
```php
// ❌ VULNERABLE
echo "Hello, " . $_GET['name'];

// ✅ FIXED
echo "Hello, " . htmlspecialchars($_GET['name'], ENT_QUOTES, 'UTF-8');
```

### File Upload Validation
```php
// ❌ VULNERABLE — trusts client-provided MIME type
if ($_FILES['file']['type'] == 'image/jpeg') { ... }

// ✅ FIXED — server-side validation
$finfo = finfo_open(FILEINFO_MIME_TYPE);
$mime = finfo_file($finfo, $_FILES['file']['tmp_name']);
$allowed = ['image/jpeg', 'image/png', 'image/gif'];
if (!in_array($mime, $allowed)) die('Invalid file type');
```

### CSRF Protection (non-WordPress PHP)
```php
// Generate token
$_SESSION['csrf_token'] = bin2hex(random_bytes(32));

// Validate on POST
if (!hash_equals($_SESSION['csrf_token'], $_POST['csrf_token'])) {
    http_response_code(403);
    die('CSRF validation failed');
}
```

### PHP Configuration Flags to Check (php.ini)
```ini
expose_php = Off           ; hides PHP version in headers
display_errors = Off       ; never show errors in production
log_errors = On            ; log them instead
allow_url_fopen = Off      ; prevents SSRF via file functions
allow_url_include = Off    ; prevents remote file inclusion
```
