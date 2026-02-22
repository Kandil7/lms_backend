import http from "k6/http";
import { check, sleep } from "k6";

const baseUrl = __ENV.BASE_URL || "http://localhost:8000";
const hostHeader = __ENV.HOST_HEADER || "";
const authEnabled = String(__ENV.AUTH_ENABLED || "false").toLowerCase() === "true";
const studentEmail = __ENV.STUDENT_EMAIL || "student@lms.local";
const studentPassword = __ENV.STUDENT_PASSWORD || "StudentPass123";

const commonHeaders = hostHeader ? { Host: hostHeader } : {};

export const options = {
  vus: Number(__ENV.VUS || 10),
  duration: __ENV.DURATION || "30s",
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
};

export default function () {
  const readyRes = http.get(`${baseUrl}/api/v1/ready`, {
    headers: commonHeaders,
  });
  check(readyRes, {
    "ready status is 200": (r) => r.status === 200,
  });

  if (authEnabled) {
    const loginPayload = JSON.stringify({
      email: studentEmail,
      password: studentPassword,
    });
    const loginRes = http.post(`${baseUrl}/api/v1/auth/login`, loginPayload, {
      headers: { ...commonHeaders, "Content-Type": "application/json" },
    });

    const loginOk = check(loginRes, {
      "login status is 200": (r) => r.status === 200,
      "login has access token": (r) => {
        try {
          const body = r.json();
          return !!body?.tokens?.access_token;
        } catch (_) {
          return false;
        }
      },
    });

    if (loginOk) {
      const accessToken = loginRes.json("tokens.access_token");
      const dashboardRes = http.get(`${baseUrl}/api/v1/analytics/my-dashboard`, {
        headers: { ...commonHeaders, Authorization: `Bearer ${accessToken}` },
      });
      check(dashboardRes, {
        "dashboard status is 200": (r) => r.status === 200,
      });
    }
  }

  sleep(1);
}
