-- PostgreSQL schema reference for the UML domain. Alembic is authoritative.
CREATE TABLE users (
  user_id SERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(32) NOT NULL CHECK (role IN ('Campus User','Administrator')),
  verification_status VARCHAR(20) NOT NULL CHECK (verification_status IN ('Unverified','Verified')),
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE lost_reports (
  report_id SERIAL PRIMARY KEY,
  owner_id INTEGER NOT NULL REFERENCES users(user_id),
  category VARCHAR(100) NOT NULL,
  description TEXT NOT NULL,
  location VARCHAR(255) NOT NULL,
  date_lost DATE NOT NULL,
  status VARCHAR(32) NOT NULL CHECK (status IN ('Pending Approval','Active','Rejected','Match Found','Claim Requested','Approved for Return','Returned','Closed')),
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE found_reports (
  report_id SERIAL PRIMARY KEY,
  finder_id INTEGER NOT NULL REFERENCES users(user_id),
  category VARCHAR(100) NOT NULL,
  description TEXT NOT NULL,
  found_location VARCHAR(255) NOT NULL,
  date_found DATE NOT NULL,
  custody_location VARCHAR(255),
  status VARCHAR(32) NOT NULL CHECK (status IN ('Pending Approval','Active','Rejected','Match Found','Claim Requested','Approved for Return','Returned','Closed')),
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE matches (
  match_id SERIAL PRIMARY KEY,
  lost_report_id INTEGER NOT NULL REFERENCES lost_reports(report_id),
  found_report_id INTEGER NOT NULL REFERENCES found_reports(report_id),
  score FLOAT NOT NULL,
  confidence VARCHAR(10) NOT NULL CHECK (confidence IN ('High','Medium','Low')),
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  status VARCHAR(20) NOT NULL DEFAULT 'Match Found' CHECK (status = 'Match Found'),
  UNIQUE (lost_report_id, found_report_id)
);

CREATE TABLE claims (
  claim_id SERIAL PRIMARY KEY,
  report_id INTEGER NOT NULL REFERENCES found_reports(report_id),
  claimant_id INTEGER NOT NULL REFERENCES users(user_id),
  proof_reference TEXT NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending','Approved for Return','Rejected')),
  reviewer_id INTEGER REFERENCES users(user_id),
  decision_comment TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  decided_at TIMESTAMP
);

CREATE TABLE notifications (
  notification_id SERIAL PRIMARY KEY,
  recipient_id INTEGER NOT NULL REFERENCES users(user_id),
  type VARCHAR(60) NOT NULL,
  message TEXT NOT NULL,
  read_at TIMESTAMP,
  delivery_status VARCHAR(12) NOT NULL DEFAULT 'Pending' CHECK (delivery_status IN ('Pending','Sent','Failed')),
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE audit_events (
  event_id SERIAL PRIMARY KEY,
  actor_id INTEGER REFERENCES users(user_id),
  action VARCHAR(120) NOT NULL,
  entity_type VARCHAR(60) NOT NULL,
  entity_id INTEGER NOT NULL,
  timestamp TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE status_history (
  history_id SERIAL PRIMARY KEY,
  entity_type VARCHAR(60) NOT NULL,
  entity_id INTEGER NOT NULL,
  old_status VARCHAR(32) NOT NULL,
  new_status VARCHAR(32) NOT NULL,
  changed_by INTEGER REFERENCES users(user_id),
  changed_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Transitional tables retain old REST clients/data until the legacy API is retired.
CREATE TABLE item_reports (
  id SERIAL PRIMARY KEY,
  owner_id INTEGER NOT NULL REFERENCES users(user_id),
  kind VARCHAR(10) NOT NULL,
  item_name VARCHAR(160) NOT NULL,
  category VARCHAR(100) NOT NULL,
  description TEXT NOT NULL,
  occurred_at TIMESTAMP NOT NULL,
  location VARCHAR(255) NOT NULL,
  custody_location VARCHAR(255),
  contact_email VARCHAR(255) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'Pending Approval',
  moderation_comment TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT now()
);
CREATE TABLE item_images (
  id SERIAL PRIMARY KEY,
  report_id INTEGER NOT NULL REFERENCES item_reports(id) ON DELETE CASCADE,
  filename VARCHAR(255) NOT NULL
);
CREATE TABLE audit_logs (
  id SERIAL PRIMARY KEY,
  actor_id INTEGER REFERENCES users(user_id),
  action VARCHAR(120) NOT NULL,
  entity_type VARCHAR(60) NOT NULL,
  entity_id INTEGER NOT NULL,
  detail TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT now()
);
