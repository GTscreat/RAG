--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: content; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.content (
    id integer NOT NULL,
    website character varying,
    title character varying,
    content text,
    url character varying,
    meta jsonb,
    published_at character varying
);


ALTER TABLE public.content OWNER TO postgres;

--
-- Name: content_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.content_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.content_id_seq OWNER TO postgres;

--
-- Name: content_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.content_id_seq OWNED BY public.content.id;


--
-- Name: embeddings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.embeddings (
    id integer NOT NULL,
    article_id integer,
    website character varying,
    title character varying,
    published_at character varying,
    url character varying,
    meta jsonb,
    chunk_content text,
    chunk_start integer,
    chunk_end integer,
    embedding bytea
);


ALTER TABLE public.embeddings OWNER TO postgres;

--
-- Name: embeddings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.embeddings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.embeddings_id_seq OWNER TO postgres;

--
-- Name: embeddings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.embeddings_id_seq OWNED BY public.embeddings.id;


--
-- Name: entities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.entities (
    id integer NOT NULL,
    entity_group character varying,
    score real,
    word character varying,
    ner_score real,
    category_id integer
);


ALTER TABLE public.entities OWNER TO postgres;

--
-- Name: entities_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.entities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.entities_id_seq OWNER TO postgres;

--
-- Name: entities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.entities_id_seq OWNED BY public.entities.id;


--
-- Name: entity_categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.entity_categories (
    id integer NOT NULL,
    code integer,
    path character varying,
    ner_category_index integer,
    ner_category_opp_index integer
);


ALTER TABLE public.entity_categories OWNER TO postgres;

--
-- Name: entity_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.entity_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.entity_categories_id_seq OWNER TO postgres;

--
-- Name: entity_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.entity_categories_id_seq OWNED BY public.entity_categories.id;


--
-- Name: ner_rating; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ner_rating (
    word character varying NOT NULL,
    score real
);


ALTER TABLE public.ner_rating OWNER TO postgres;

--
-- Name: ner_results; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ner_results (
    id integer NOT NULL,
    entities jsonb
);


ALTER TABLE public.ner_results OWNER TO postgres;

--
-- Name: parameters; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parameters (
    id integer NOT NULL,
    category character varying,
    aver_embedding bytea,
    similarity jsonb
);


ALTER TABLE public.parameters OWNER TO postgres;

--
-- Name: processed; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.processed (
    base_id integer NOT NULL,
    title character varying,
    generated_content text,
    published character varying,
    title_r character varying,
    generated_content_r text,
    published_r character varying
);


ALTER TABLE public.processed OWNER TO postgres;

--
-- Name: ranks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ranks (
    id integer NOT NULL,
    topic_importance real,
    ner_content_importance real,
    frequency_importance real,
    source_importance real,
    total_score real
);


ALTER TABLE public.ranks OWNER TO postgres;

--
-- Name: top; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.top (
    id integer NOT NULL,
    total_score real,
    ai_score real,
    urgency integer,
    sentiment character varying,
    geopolitical character varying,
    final_score real
);


ALTER TABLE public.top OWNER TO postgres;

--
-- Name: content id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.content ALTER COLUMN id SET DEFAULT nextval('public.content_id_seq'::regclass);


--
-- Name: embeddings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.embeddings ALTER COLUMN id SET DEFAULT nextval('public.embeddings_id_seq'::regclass);


--
-- Name: entities id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entities ALTER COLUMN id SET DEFAULT nextval('public.entities_id_seq'::regclass);


--
-- Name: entity_categories id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entity_categories ALTER COLUMN id SET DEFAULT nextval('public.entity_categories_id_seq'::regclass);


--
-- Name: content content_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.content
    ADD CONSTRAINT content_pkey PRIMARY KEY (id);


--
-- Name: embeddings embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.embeddings
    ADD CONSTRAINT embeddings_pkey PRIMARY KEY (id);


--
-- Name: entities entities_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entities
    ADD CONSTRAINT entities_pkey PRIMARY KEY (id);


--
-- Name: entity_categories entity_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entity_categories
    ADD CONSTRAINT entity_categories_pkey PRIMARY KEY (id);


--
-- Name: ner_rating ner_rating_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ner_rating
    ADD CONSTRAINT ner_rating_pkey PRIMARY KEY (word);


--
-- Name: ner_results ner_results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ner_results
    ADD CONSTRAINT ner_results_pkey PRIMARY KEY (id);


--
-- Name: parameters parameters_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parameters
    ADD CONSTRAINT parameters_pkey PRIMARY KEY (id);


--
-- Name: processed processed_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.processed
    ADD CONSTRAINT processed_pkey PRIMARY KEY (base_id);


--
-- Name: ranks ranks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ranks
    ADD CONSTRAINT ranks_pkey PRIMARY KEY (id);


--
-- Name: top top_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.top
    ADD CONSTRAINT top_pkey PRIMARY KEY (id);


--
-- Name: ix_content_published_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_content_published_at ON public.content USING btree (published_at);


--
-- Name: ix_content_website; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_content_website ON public.content USING btree (website);


--
-- Name: ix_embeddings_article_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_embeddings_article_id ON public.embeddings USING btree (article_id);


--
-- Name: ix_processed_published; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_processed_published ON public.processed USING btree (published);


--
-- Name: ix_processed_published_r; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_processed_published_r ON public.processed USING btree (published_r);


--
-- Name: embeddings embeddings_article_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.embeddings
    ADD CONSTRAINT embeddings_article_id_fkey FOREIGN KEY (article_id) REFERENCES public.content(id) ON DELETE CASCADE;


--
-- Name: entities entities_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entities
    ADD CONSTRAINT entities_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.entity_categories(id) ON DELETE SET NULL;


--
-- Name: ner_results ner_results_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ner_results
    ADD CONSTRAINT ner_results_id_fkey FOREIGN KEY (id) REFERENCES public.content(id) ON DELETE CASCADE;


--
-- Name: parameters parameters_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parameters
    ADD CONSTRAINT parameters_id_fkey FOREIGN KEY (id) REFERENCES public.content(id) ON DELETE CASCADE;


--
-- Name: processed processed_base_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.processed
    ADD CONSTRAINT processed_base_id_fkey FOREIGN KEY (base_id) REFERENCES public.content(id) ON DELETE CASCADE;


--
-- Name: ranks ranks_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ranks
    ADD CONSTRAINT ranks_id_fkey FOREIGN KEY (id) REFERENCES public.content(id) ON DELETE CASCADE;


--
-- Name: top top_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.top
    ADD CONSTRAINT top_id_fkey FOREIGN KEY (id) REFERENCES public.content(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

