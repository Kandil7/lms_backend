import http from "k6/http";
import { check, sleep } from "k6";

const baseUrl = __ENV.BASE_URL || "http://localhost:8000";
const hostHeader = __ENV.HOST_HEADER || "";

const studentEmail = __ENV.STUDENT_EMAIL || "student@lms.local";
const studentPassword = __ENV.STUDENT_PASSWORD || "StudentPass123";
const instructorEmail = __ENV.INSTRUCTOR_EMAIL || "instructor@lms.local";
const instructorPassword = __ENV.INSTRUCTOR_PASSWORD || "InstructorPass123";
const adminEmail = __ENV.ADMIN_EMAIL || "admin@lms.local";
const adminPassword = __ENV.ADMIN_PASSWORD || "AdminPass123";

const duration = __ENV.DURATION || "5m";
const studentRate = Number(__ENV.STUDENT_RATE || 5);
const instructorRate = Number(__ENV.INSTRUCTOR_RATE || 2);
const adminRate = Number(__ENV.ADMIN_RATE || 1);
const healthVus = Number(__ENV.HEALTH_VUS || 2);

const commonHeaders = hostHeader ? { Host: hostHeader } : {};

function jsonHeaders(extra = {}) {
  return { ...commonHeaders, "Content-Type": "application/json", ...extra };
}

function login(email, password) {
  const payload = JSON.stringify({ email, password });
  const res = http.post(`${baseUrl}/api/v1/auth/login`, payload, {
    headers: jsonHeaders(),
  });

  const ok = check(res, {
    "login status is 200": (r) => r.status === 200,
    "login returns access token": (r) => {
      try {
        return !!r.json("tokens.access_token");
      } catch (_) {
        return false;
      }
    },
  });

  if (!ok) {
    return "";
  }

  return res.json("tokens.access_token");
}

export const options = {
  scenarios: {
    health_probe: {
      executor: "constant-vus",
      exec: "healthProbe",
      vus: healthVus,
      duration,
    },
    student_journey: {
      executor: "constant-arrival-rate",
      exec: "studentJourney",
      rate: studentRate,
      timeUnit: "1s",
      duration,
      preAllocatedVUs: 10,
      maxVUs: 80,
    },
    instructor_journey: {
      executor: "constant-arrival-rate",
      exec: "instructorJourney",
      rate: instructorRate,
      timeUnit: "1s",
      duration,
      preAllocatedVUs: 5,
      maxVUs: 40,
    },
    admin_journey: {
      executor: "constant-arrival-rate",
      exec: "adminJourney",
      rate: adminRate,
      timeUnit: "1s",
      duration,
      preAllocatedVUs: 3,
      maxVUs: 20,
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.02"],
    http_req_duration: ["p(95)<800"],
    checks: ["rate>0.98"],
  },
};

export function healthProbe() {
  const readyRes = http.get(`${baseUrl}/api/v1/ready`, {
    headers: commonHeaders,
  });
  check(readyRes, {
    "ready status is 200": (r) => r.status === 200,
  });
  sleep(1);
}

export function studentJourney() {
  const token = login(studentEmail, studentPassword);
  if (!token) {
    sleep(1);
    return;
  }

  const authHeaders = { ...commonHeaders, Authorization: `Bearer ${token}` };

  const dashboardRes = http.get(`${baseUrl}/api/v1/analytics/my-dashboard`, {
    headers: authHeaders,
  });
  check(dashboardRes, {
    "student dashboard status is 200": (r) => r.status === 200,
  });

  const coursesRes = http.get(`${baseUrl}/api/v1/enrollments/my-courses`, {
    headers: authHeaders,
  });
  check(coursesRes, {
    "student courses status is 200": (r) => r.status === 200,
  });

  sleep(1);
}

export function instructorJourney() {
  const token = login(instructorEmail, instructorPassword);
  if (!token) {
    sleep(1);
    return;
  }

  const authHeaders = { ...commonHeaders, Authorization: `Bearer ${token}` };

  const coursesRes = http.get(`${baseUrl}/api/v1/courses`, {
    headers: authHeaders,
  });
  check(coursesRes, {
    "instructor courses status is 200": (r) => r.status === 200,
  });

  sleep(1);
}

export function adminJourney() {
  const token = login(adminEmail, adminPassword);
  if (!token) {
    sleep(1);
    return;
  }

  const authHeaders = { ...commonHeaders, Authorization: `Bearer ${token}` };

  const usersRes = http.get(`${baseUrl}/api/v1/users`, {
    headers: authHeaders,
  });
  check(usersRes, {
    "admin users status is 200": (r) => r.status === 200,
  });

  sleep(1);
}

