import re

with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/jobs.html', 'r') as f:
    content = f.read()

# Add CSS
spinner_css = '''
    .btn-spinner {
      width: 16px;
      height: 16px;
      border: 2px solid rgba(255, 255, 255, 0.4);
      border-top-color: #ffffff;
      border-radius: 50%;
      animation: spin 0.85s linear infinite;
      display: inline-block;
      vertical-align: middle;
      margin-right: 8px;
    }
'''
content = content.replace('    .spinner {', spinner_css + '\n    .spinner {')


# Update handleSignup
signup_new = '''
    async function handleSignup(e) {
      e.preventDefault();
      const name = document.getElementById('suName').value;
      const email = document.getElementById('suEmail').value;
      const pass = document.getElementById('suPass').value;
      pendingEmail = email;

      const btn = document.querySelector('#signupForm .auth-submit-btn');
      const originalText = btn.innerHTML;
      btn.innerHTML = '<span class="btn-spinner"></span> Sending OTP...';
      btn.disabled = true;
      btn.style.opacity = '0.8';

      try {
        const res = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, password: pass })
        });
        const data = await res.json();
        if (res.ok && data.success) {
          document.getElementById('signupForm').style.display = 'none';
          document.getElementById('otpForm').style.display = 'block';
          document.getElementById('otpNotice').innerHTML = `A 6-digit verification code has been sent to <strong>${escapeHtml(pendingEmail)}</strong>. Please check your inbox or spam folder.`;
          document.getElementById('otpCode').value = '';
          document.getElementById('otpCode').focus();
        } else {
          showAuthError(data.detail || data.message);
        }
      } catch (err) {
        showAuthError('Connection error.');
      } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
        btn.style.opacity = '1';
      }
    }
'''
content = re.sub(r'async function handleSignup\(e\) \{.*?\}\n', signup_new.strip() + '\n', content, flags=re.DOTALL)


# Update handleVerifyOtp
verify_new = '''
    async function handleVerifyOtp(e) {
      e.preventDefault();
      const code = document.getElementById('otpCode').value;

      const btn = document.querySelector('#otpForm .auth-submit-btn');
      const originalText = btn.innerHTML;
      btn.innerHTML = '<span class="btn-spinner"></span> Verifying...';
      btn.disabled = true;
      btn.style.opacity = '0.8';

      try {
        const res = await fetch('/api/auth/verify_otp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: pendingEmail, otp: code })
        });
        const data = await res.json();
        if (res.ok && data.success) {
          closeAuthModal();
          checkAuthStatus();
          executeSearch(1);
        } else {
          showAuthError(data.detail || data.message);
        }
      } catch (err) {
        showAuthError('Verification error.');
      } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
        btn.style.opacity = '1';
      }
    }
'''
content = re.sub(r'async function handleVerifyOtp\(e\) \{.*?\}\n', verify_new.strip() + '\n', content, flags=re.DOTALL)


# Update handleLogin
login_new = '''
    async function handleLogin(e) {
      e.preventDefault();
      const email = document.getElementById('liEmail').value;
      const pass = document.getElementById('liPass').value;

      const btn = document.querySelector('#loginForm .auth-submit-btn');
      const originalText = btn.innerHTML;
      btn.innerHTML = '<span class="btn-spinner"></span> Logging In...';
      btn.disabled = true;
      btn.style.opacity = '0.8';

      try {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password: pass })
        });
        const data = await res.json();
        if (res.ok && data.success) {
          closeAuthModal();
          checkAuthStatus();
          executeSearch(1);
        } else {
          showAuthError(data.detail || data.message);
        }
      } catch (err) {
        showAuthError('Login error.');
      } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
        btn.style.opacity = '1';
      }
    }
'''
content = re.sub(r'async function handleLogin\(e\) \{.*?\}\n', login_new.strip() + '\n', content, flags=re.DOTALL)


with open('/Users/iamrj846/Desktop/iamrj846.github.io/frontend/jobs.html', 'w') as f:
    f.write(content)
print("Updated Auth forms with loading spinners")
