CREATE TABLE public.applied_jobs (
  id text NOT NULL,
  user_id text,
  job_id text,
  job_title text,
  job_company text,
  applied_at timestamp without time zone DEFAULT now(),
  match_score double precision,
  CONSTRAINT applied_jobs_pkey PRIMARY KEY (id),
  CONSTRAINT applied_jobs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.resumes (
  id text NOT NULL,
  user_id text,
  original_text text,
  parsed_skills text,
  parsed_experience integer,
  uploaded_at timestamp without time zone DEFAULT now(),
  CONSTRAINT resumes_pkey PRIMARY KEY (id),
  CONSTRAINT resumes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.sessions (
  id text NOT NULL DEFAULT (gen_random_uuid())::text,
  user_id text NOT NULL,
  token text NOT NULL UNIQUE,
  created_at timestamp without time zone DEFAULT now(),
  expires_at timestamp without time zone NOT NULL,
  CONSTRAINT sessions_pkey PRIMARY KEY (id),
  CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.users (
  id text NOT NULL,
  name text,
  age integer,
  gender text,
  location text,
  experience text,
  target_roles text,
  employment_type text,
  preferred_companies text,
  created_at timestamp without time zone DEFAULT now(),
  email text,
  password text,
  CONSTRAINT users_pkey PRIMARY KEY (id)
);