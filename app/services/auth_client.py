import os
import sys
import json
import threading
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from queue import Queue, Empty

from PySide6.QtCore import QSettings

# Debug: print all untuk lihat error detail
print("[AUTH] Starting supabase import...", flush=True)
create_client = None
try:
    print("[AUTH] Step 1: importing supabase module...", flush=True)
    import supabase
    print(f"[AUTH] Step 2: supabase module loaded: {supabase.__file__}", flush=True)
    from supabase import create_client
    print("[AUTH] Step 3: create_client imported successfully", flush=True)
except Exception as e:
    print(f"[AUTH] IMPORT FAILED: {type(e).__name__}: {e}", flush=True)
    traceback.print_exc()
    create_client = None

# Hardcoded production credentials
# Note: SUPABASE_ANON_KEY is designed to be public-facing (client-side)
# Security is handled by Row Level Security (RLS) in Supabase
SUPABASE_URL = "https://mkcl....example"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5c.... example"


class OAuthCallbackServer:
    def __init__(self, host="127.0.0.1", port=8765):
        self.host = host
        self.port = port
        self._queue = Queue()
        self._server = None
        self._thread = None

    def _make_handler(self):
        queue_ref = self._queue

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                return

            def do_GET(self):
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                code = params.get("code", [""])[0]
                error = params.get("error", [""])[0]
                if code:
                    queue_ref.put({"code": code})
                elif error:
                    queue_ref.put({"error": error})
                else:
                    queue_ref.put({"error": "missing_code"})

                body = (
                    "<html><body style='font-family:sans-serif;'>"
                    "<h2>Login selesai</h2>"
                    "<p>Silakan kembali ke aplikasi.</p>"
                    "</body></html>"
                )
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(body.encode("utf-8"))

        return Handler

    def start(self):
        handler = self._make_handler()
        self._server = HTTPServer((self.host, self.port), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def wait_for_result(self, timeout=180):
        try:
            return self._queue.get(timeout=timeout)
        except Empty:
            return {"error": "timeout"}

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None


class AuthClient:
    def __init__(self):
        # Langsung pakai hardcoded credentials
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_ANON_KEY
        self.settings = QSettings("GalaxyStream", "GalaxyStream")
        self.client = None
        self.available = False

        print(f"[AUTH] Initializing AuthClient...", flush=True)
        print(f"[AUTH] SUPABASE_URL: {self.supabase_url[:30]}...", flush=True)

        if create_client and self.supabase_url and self.supabase_key:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                self.available = True
                print(f"[AUTH] Supabase client initialized successfully", flush=True)
            except Exception as e:
                print(f"[AUTH] Failed to initialize Supabase client: {e}", flush=True)
        else:
            if not create_client:
                print(f"[AUTH] Supabase library not available", flush=True)
            if not self.supabase_url or not self.supabase_key:
                print(f"[AUTH] Supabase credentials not configured", flush=True)

    def is_available(self):
        return self.available


    def _get_attr(self, resp, name):
        if resp is None:
            return None
        if hasattr(resp, name):
            return getattr(resp, name)
        if isinstance(resp, dict):
            return resp.get(name)
        return None

    def _make_json_serializable(self, obj):
        """
        Convert object menjadi JSON-serializable recursively.

        Args:
            obj: Any object

        Returns:
            JSON-serializable version of object
        """
        import datetime

        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item) for item in obj]
        elif hasattr(obj, 'dict'):
            try:
                return self._make_json_serializable(obj.dict())
            except:
                pass
        elif hasattr(obj, '__dict__'):
            return self._make_json_serializable(obj.__dict__)
        else:
            # Convert to string as last resort
            return str(obj)

    def _session_to_dict(self, session):
        """
        Konversi session object ke dictionary.

        Mencoba berbagai cara untuk mengkonversi session object dari Supabase
        menjadi dictionary Python yang bisa di-serialize ke JSON.

        Args:
            session: Session object dari Supabase

        Returns:
            Dictionary berisi session data, atau None jika gagal
        """
        print(f"[AUTH] Converting session type: {type(session)}", flush=True)

        if session is None:
            return None

        if isinstance(session, dict):
            return self._make_json_serializable(session)

        # Try model_dump() for Pydantic v2
        if hasattr(session, "model_dump"):
            try:
                result = session.model_dump()
                print(f"[AUTH]  Converted using model_dump()", flush=True)
                return self._make_json_serializable(result)
            except Exception as e:
                print(f"[AUTH]  model_dump() failed: {e}", flush=True)

        # Try dict() for Pydantic v1
        if hasattr(session, "dict"):
            try:
                result = session.dict()
                print(f"[AUTH]  Converted using dict()", flush=True)
                return self._make_json_serializable(result)
            except Exception as e:
                print(f"[AUTH]  dict() failed: {e}", flush=True)

        # Try to convert object attributes to dict
        if hasattr(session, "__dict__"):
            try:
                result = dict(session.__dict__)
                print(f"[AUTH]  Converted using __dict__", flush=True)
                return self._make_json_serializable(result)
            except Exception as e:
                print(f"[AUTH]  __dict__ failed: {e}", flush=True)

        # Last resort: manual attribute extraction
        try:
            result = {}
            attrs = ["access_token", "refresh_token", "expires_in", "expires_at", "token_type", "user"]
            for attr in attrs:
                if hasattr(session, attr):
                    val = getattr(session, attr)
                    # Convert user object to dict if needed
                    if attr == "user" and val:
                        if hasattr(val, "dict"):
                            val = val.dict()
                        elif hasattr(val, "__dict__"):
                            val = dict(val.__dict__)
                    result[attr] = val

            if result.get("access_token"):
                print(f"[AUTH]  Manual extraction successful", flush=True)
                return self._make_json_serializable(result)
            print(f"[AUTH]  No access_token found", flush=True)
        except Exception as e:
            print(f"[AUTH]  Manual extraction failed: {e}", flush=True)

        return None

    def save_session(self, session):
        """
        Menyimpan session ke QSettings.

        Args:
            session: Session object yang akan disimpan

        Raises:
            RuntimeError: Jika gagal menyimpan session
        """
        print(f"[AUTH] save_session called", flush=True)

        data = self._session_to_dict(session)

        # Handle string edge case
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception as e:
                print(f"[AUTH] Failed to parse string as JSON: {e}", flush=True)
                data = None

        # Validate data is a dict with access_token
        if not isinstance(data, dict):
            raise RuntimeError(f"Session conversion failed. Got: {type(data)}")

        if not data.get("access_token"):
            raise RuntimeError(f"Missing access_token. Keys: {list(data.keys())}")

        # Try to serialize to JSON
        try:
            json_str = json.dumps(data)
            print(f"[AUTH] JSON serialization successful: {len(json_str)} chars", flush=True)
        except TypeError as e:
            # If JSON serialization fails, log what's not serializable
            print(f"[AUTH]  JSON serialization failed: {e}", flush=True)
            print(f"[AUTH] Problematic data type: {type(data)}", flush=True)
            print(f"[AUTH] Data keys: {list(data.keys())}", flush=True)

            # Try to identify non-serializable items
            for key, value in data.items():
                try:
                    json.dumps({key: value})
                except TypeError:
                    print(f"[AUTH] Non-serializable key: {key}, type: {type(value)}", flush=True)

            raise RuntimeError(f"Failed to serialize session to JSON: {e}")

        # Save to QSettings
        try:
            self.settings.setValue("auth_session", json_str)
            print(f"[AUTH]  Session saved to QSettings", flush=True)
        except Exception as e:
            print(f"[AUTH] Failed to save to QSettings: {e}", flush=True)
            raise RuntimeError(f"Failed to save session: {e}")

    def clear_session(self):
        self.settings.remove("auth_session")

    def _load_session_data(self):
        raw = self.settings.value("auth_session", "")
        if not raw:
            return None
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, str):
                try:
                    loaded = json.loads(loaded)
                except Exception:
                    return None
            return loaded
        except Exception:
            return None

    def restore_session(self):
        if not self.available:
            return None
        data = self._load_session_data()
        if not data or not isinstance(data, dict):
            return None
        access = data.get("access_token")
        refresh = data.get("refresh_token")
        if not access or not refresh:
            return None
        try:
            self.client.auth.set_session(access, refresh)
            return self.client.auth.get_session()
        except Exception:
            return None

    def has_session(self):
        if not self.available:
            return False
        try:
            session = self.client.auth.get_session()
            return session is not None
        except Exception:
            return False

    def get_session(self):
        if not self.available:
            return None
        try:
            return self.client.auth.get_session()
        except Exception:
            return None

    def sign_in_email(self, email, password):
        """
        Sign in dengan email dan password.

        Args:
            email: Email user
            password: Password user

        Returns:
            Session object jika berhasil

        Raises:
            RuntimeError: Jika Supabase client tidak dikonfigurasi atau login gagal
        """
        if not self.available:
            raise RuntimeError("Supabase client not configured")

        print(f"[AUTH] Signing in: {email}", flush=True)

        try:
            resp = self.client.auth.sign_in_with_password({"email": email, "password": password})
            print(f"[AUTH] Response type: {type(resp)}", flush=True)
            print(f"[AUTH] Full response: {resp}", flush=True)

            # Check if there's an error in response
            error = self._get_attr(resp, "error")
            if error:
                error_msg = str(error)
                print(f"[AUTH]  Error in response: {error_msg}", flush=True)

                # Check for common error cases
                if "invalid" in error_msg.lower() and "credentials" in error_msg.lower():
                    raise RuntimeError("Invalid email or password")
                elif "email not confirmed" in error_msg.lower():
                    raise RuntimeError("Email not confirmed. Please check your email and click the confirmation link.")
                elif "user not found" in error_msg.lower():
                    raise RuntimeError("No account found with this email")
                else:
                    raise RuntimeError(f"Login failed: {error_msg}")

            session = self._get_attr(resp, "session")
            print(f"[AUTH] Session from response: {type(session)}", flush=True)

            if not session:
                print(f"[AUTH] No session in response, trying get_session()...", flush=True)
                try:
                    session = self.client.auth.get_session()
                    print(f"[AUTH] Session from get_session(): {type(session)}", flush=True)
                except Exception as e:
                    print(f"[AUTH] get_session() failed: {e}", flush=True)
                    session = None

            if not session:
                # Check if user exists but email not confirmed
                user = self._get_attr(resp, "user")
                if user:
                    print(f"[AUTH] User exists but no session - email might not be confirmed", flush=True)
                    raise RuntimeError("Email not confirmed. Please check your email and click the confirmation link.")
                else:
                    raise RuntimeError("Login failed - no session returned. Please check your credentials.")

            # Save session
            print(f"[AUTH] Saving session...", flush=True)
            self.save_session(session)
            print(f"[AUTH]  Sign in successful", flush=True)
            return session

        except RuntimeError:
            # Re-raise RuntimeError as-is (already formatted)
            raise
        except Exception as e:
            print(f"[AUTH]  Sign in failed with exception: {type(e).__name__}", flush=True)
            print(f"[AUTH] Exception message: {str(e)}", flush=True)

            # Try to extract meaningful error message
            error_msg = str(e)
            if "Invalid login credentials" in error_msg or "invalid_grant" in error_msg:
                raise RuntimeError("Invalid email or password. Please check and try again.")
            elif "Email not confirmed" in error_msg:
                raise RuntimeError("Email not confirmed. Please check your email and click the confirmation link.")
            else:
                import traceback
                traceback.print_exc()
                raise RuntimeError(f"Login failed: {error_msg}")

    def sign_up_email(self, email, password):
        """
        Sign up / create account dengan email dan password.

        Args:
            email: Email user
            password: Password user

        Returns:
            Session object jika berhasil (atau None jika perlu email confirmation)

        Raises:
            RuntimeError: Jika Supabase client tidak dikonfigurasi atau signup gagal
        """
        if not self.available:
            raise RuntimeError("Supabase client not configured")

        print(f"[AUTH] Creating account: {email}", flush=True)

        try:
            resp = self.client.auth.sign_up({"email": email, "password": password})
            print(f"[AUTH] Signup response type: {type(resp)}", flush=True)
            print(f"[AUTH] Signup response: {resp}", flush=True)

            # Check if response has user info
            user = self._get_attr(resp, "user")
            print(f"[AUTH] User from response: {type(user)}, {user}", flush=True)

            session = self._get_attr(resp, "session")
            print(f"[AUTH] Session from signup response: {type(session)}", flush=True)

            if not session:
                print(f"[AUTH] No session in response, trying get_session()...", flush=True)
                try:
                    session = self.client.auth.get_session()
                    print(f"[AUTH] Session from get_session(): {type(session)}", flush=True)
                except Exception as e:
                    print(f"[AUTH] get_session() failed: {e}", flush=True)
                    session = None

            if session:
                print(f"[AUTH] Session found, saving...", flush=True)
                self.save_session(session)
                print(f"[AUTH]  Sign up successful with session", flush=True)
                return session
            else:
                # No session means email confirmation required
                if user:
                    print(f"[AUTH] WARNING: Account created but email confirmation required", flush=True)
                    print(f"[AUTH] User ID: {self._get_attr(user, 'id')}", flush=True)
                    print(f"[AUTH] Check email for confirmation link", flush=True)
                    # Return None but don't raise error - this is expected behavior
                    return None
                else:
                    print(f"[AUTH]  No session and no user - signup may have failed", flush=True)
                    raise RuntimeError("Signup failed - no user or session returned")

        except Exception as e:
            print(f"[AUTH]  Sign up failed: {e}", flush=True)
            import traceback
            traceback.print_exc()
            raise

    def sign_out(self):
        if not self.available:
            return
        try:
            self.client.auth.sign_out()
        finally:
            self.clear_session()

    def start_google_oauth(self, redirect_port=8765):
        if not self.available:
            raise RuntimeError("Supabase client not configured")

        redirect_url = f"http://127.0.0.1:{redirect_port}/callback"
        server = OAuthCallbackServer(port=redirect_port)
        server.start()

        resp = self.client.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": redirect_url}
        })

        auth_url = self._get_attr(resp, "url")
        if not auth_url:
            server.stop()
        return auth_url, server

    def exchange_code_for_session(self, code):
        """
        Exchange OAuth code untuk mendapatkan session.

        Args:
            code: Authorization code dari OAuth callback

        Returns:
            Session object jika berhasil

        Raises:
            RuntimeError: Jika Supabase client tidak dikonfigurasi atau exchange gagal
        """
        if not self.available:
            raise RuntimeError("Supabase client not configured")

        print(f"[AUTH] Exchanging OAuth code for session", flush=True)

        try:
            # exchange_code_for_session expects a dict with auth_code
            resp = self.client.auth.exchange_code_for_session({"auth_code": code})
            print(f"[AUTH] Exchange response type: {type(resp)}", flush=True)

            # Check for error
            error = self._get_attr(resp, "error")
            if error:
                error_msg = str(error)
                print(f"[AUTH]  Error in exchange response: {error_msg}", flush=True)
                raise RuntimeError(f"OAuth login failed: {error_msg}")

            session = self._get_attr(resp, "session")
            print(f"[AUTH] Session from exchange: {type(session)}", flush=True)

            if not session:
                print(f"[AUTH] No session in response, trying get_session()...", flush=True)
                try:
                    session = self.client.auth.get_session()
                    print(f"[AUTH] Session from get_session(): {type(session)}", flush=True)
                except Exception as e:
                    print(f"[AUTH] get_session() failed: {e}", flush=True)
                    session = None

            if not session:
                raise RuntimeError("OAuth login failed - no session returned")

            # Save session
            print(f"[AUTH] Saving OAuth session...", flush=True)
            self.save_session(session)
            print(f"[AUTH]  OAuth login successful", flush=True)
            return session

        except RuntimeError:
            # Re-raise RuntimeError as-is
            raise
        except Exception as e:
            print(f"[AUTH]  OAuth exchange failed: {type(e).__name__}", flush=True)
            print(f"[AUTH] Exception message: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"OAuth login failed: {str(e)}")
