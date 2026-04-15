--
-- PostgreSQL database dump
--

\restrict i6OrvhNYTQbM3CznkqszENi3ZXDcTHl5XwHSBlUDJfqnqubdtj9FXm9rdw7trxX

-- Dumped from database version 15.14
-- Dumped by pg_dump version 15.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: cricket_admin
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO cricket_admin;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: cricket_admin
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: clubs; Type: TABLE; Schema: public; Owner: cricket_admin
--

CREATE TABLE public.clubs (
    id character varying(50) NOT NULL,
    season_id character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    full_name character varying(200) NOT NULL,
    country character varying(50),
    cricket_board character varying(50),
    website_url character varying(300),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.clubs OWNER TO cricket_admin;

--
-- Name: fantasy_team_players; Type: TABLE; Schema: public; Owner: cricket_admin
--

CREATE TABLE public.fantasy_team_players (
    id character varying(50) NOT NULL,
    fantasy_team_id character varying(50) NOT NULL,
    player_id character varying(50) NOT NULL,
    purchase_value double precision NOT NULL,
    is_captain boolean,
    is_vice_captain boolean,
    "position" integer,
    total_points double precision,
    added_at timestamp without time zone,
    is_wicket_keeper boolean DEFAULT false
);


ALTER TABLE public.fantasy_team_players OWNER TO cricket_admin;

--
-- Name: fantasy_teams; Type: TABLE; Schema: public; Owner: cricket_admin
--

CREATE TABLE public.fantasy_teams (
    id character varying(50) NOT NULL,
    league_id character varying(50) NOT NULL,
    user_id character varying(50) NOT NULL,
    team_name character varying(200) NOT NULL,
    budget_used double precision,
    budget_remaining double precision,
    is_finalized boolean,
    total_points double precision,
    rank integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    transfers_used integer DEFAULT 0,
    extra_transfers_granted integer DEFAULT 0
);


ALTER TABLE public.fantasy_teams OWNER TO cricket_admin;

--
-- Name: leagues; Type: TABLE; Schema: public; Owner: cricket_admin
--

CREATE TABLE public.leagues (
    id character varying(50) NOT NULL,
    season_id character varying(50) NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    league_code character varying(20) NOT NULL,
    squad_size integer,
    budget double precision,
    currency character varying(10),
    min_players_per_team integer,
    max_players_per_team integer,
    require_from_each_team boolean,
    is_public boolean,
    max_participants integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by character varying(50) NOT NULL,
    transfers_per_season integer DEFAULT 4,
    min_batsmen integer DEFAULT 3,
    min_bowlers integer DEFAULT 3,
    require_wicket_keeper boolean DEFAULT true,
    club_id character varying(50) NOT NULL
);


ALTER TABLE public.leagues OWNER TO cricket_admin;

--
-- Name: player_performances; Type: TABLE; Schema: public; Owner: cricket_admin
--

CREATE TABLE public.player_performances (
    id character varying(50) NOT NULL,
    player_id character varying(50) NOT NULL,
    fantasy_team_id character varying(50),
    league_id character varying(50),
    round_number integer,
    runs integer DEFAULT 0,
    balls_faced integer DEFAULT 0,
    is_out boolean DEFAULT false,
    wickets integer DEFAULT 0,
    overs double precision DEFAULT 0,
    runs_conceded integer DEFAULT 0,
    maidens integer DEFAULT 0,
    catches integer DEFAULT 0,
    stumpings integer DEFAULT 0,
    runouts integer DEFAULT 0,
    base_fantasy_points double precision DEFAULT 0.0,
    multiplier_applied double precision DEFAULT 1.0,
    captain_multiplier double precision DEFAULT 1.0,
    final_fantasy_points double precision DEFAULT 0.0,
    is_captain boolean DEFAULT false,
    is_vice_captain boolean DEFAULT false,
    is_wicket_keeper boolean DEFAULT false,
    match_date timestamp without time zone,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.player_performances OWNER TO cricket_admin;

--
-- Name: player_price_history; Type: TABLE; Schema: public; Owner: cricket_admin
--

CREATE TABLE public.player_price_history (
    id character varying(50) NOT NULL,
    player_id character varying(50) NOT NULL,
    old_value double precision NOT NULL,
    new_value double precision NOT NULL,
    change_reason character varying(50) NOT NULL,
    reason_details text,
    changed_at timestamp without time zone,
    changed_by character varying(50)
);


ALTER TABLE public.player_price_history OWNER TO cricket_admin;

--
-- Name: players; Type: TABLE; Schema: public; Owner: cricket_admin
--

CREATE TABLE public.players (
    id character varying(50) NOT NULL,
    club_id character varying(50) NOT NULL,
    team_id character varying(50),
    name character varying(200) NOT NULL,
    player_type character varying(50),
    fantasy_value double precision,
    value_calculation_date timestamp without time zone,
    value_manually_adjusted boolean,
    value_adjustment_reason text,
    stats json,
    performance_score double precision,
    consistency_score double precision,
    legacy_player_id character varying(100),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by character varying(50),
    multiplier double precision DEFAULT 1.0 NOT NULL,
    multiplier_updated_at timestamp without time zone,
    is_wicket_keeper boolean DEFAULT false
);


ALTER TABLE public.players OWNER TO cricket_admin;

--
-- Name: seasons; Type: TABLE; Schema: public; Owner: cricket_admin
--

CREATE TABLE public.seasons (
    id character varying(50) NOT NULL,
    year character varying(10) NOT NULL,
    name character varying(100) NOT NULL,
    start_date timestamp without time zone NOT NULL,
    end_date timestamp without time zone NOT NULL,
    description text,
    is_active boolean,
    registration_open boolean,
    scraping_enabled boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by character varying(50)
);


ALTER TABLE public.seasons OWNER TO cricket_admin;

--
-- Name: teams; Type: TABLE; Schema: public; Owner: cricket_admin
--

CREATE TABLE public.teams (
    id character varying(50) NOT NULL,
    club_id character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    level character varying(20) NOT NULL,
    tier_type character varying(50),
    value_multiplier double precision,
    points_multiplier double precision,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.teams OWNER TO cricket_admin;

--
-- Name: transfers; Type: TABLE; Schema: public; Owner: cricket_admin
--

CREATE TABLE public.transfers (
    id character varying(50) NOT NULL,
    fantasy_team_id character varying(50) NOT NULL,
    player_out_id character varying(50),
    player_in_id character varying(50) NOT NULL,
    transfer_type character varying(50) DEFAULT 'regular'::character varying,
    requires_approval boolean DEFAULT false,
    is_approved boolean DEFAULT false,
    approved_by character varying(50),
    proof_url character varying(500),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    approved_at timestamp without time zone
);


ALTER TABLE public.transfers OWNER TO cricket_admin;

--
-- Name: users; Type: TABLE; Schema: public; Owner: cricket_admin
--

CREATE TABLE public.users (
    id character varying(50) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    full_name character varying(255) NOT NULL,
    is_active boolean,
    is_verified boolean,
    is_admin boolean,
    created_at timestamp without time zone,
    last_login timestamp without time zone
);


ALTER TABLE public.users OWNER TO cricket_admin;

--
-- Data for Name: clubs; Type: TABLE DATA; Schema: public; Owner: cricket_admin
--

COPY public.clubs (id, season_id, name, full_name, country, cricket_board, website_url, created_at, updated_at) FROM stdin;
a7a580a7-7d3f-476c-82ea-afa6ae7ee276	380f5bce-e6fc-4e75-947d-617fad9d5ee8	ACC	Amsterdamsche Cricket Club	Netherlands	KNCB	https://matchcentre.kncb.nl/club/ACC	2025-11-05 20:01:41.99253	2025-11-05 20:01:41.992531
\.


--
-- Data for Name: fantasy_team_players; Type: TABLE DATA; Schema: public; Owner: cricket_admin
--

COPY public.fantasy_team_players (id, fantasy_team_id, player_id, purchase_value, is_captain, is_vice_captain, "position", total_points, added_at, is_wicket_keeper) FROM stdin;
c6ef48cc-f755-455f-9735-c2b1ed7c8e6e	a7b61896-15db-43ae-8ed9-a8f86310e919	f87a9b05-97f0-41c6-82c5-f673fcf67fe5	25	f	t	\N	1537.8663328090856	2025-11-06 17:18:32.725694	f
9e593b01-a6f8-45d7-8966-efe52d98db7e	a7b61896-15db-43ae-8ed9-a8f86310e919	e08a0b13-4bf6-4853-8d72-84273821e0c3	25	f	f	\N	1999.2125690004552	2025-11-06 17:18:28.453762	f
4cee7634-fb27-4b0c-90c6-23b36def8401	a7b61896-15db-43ae-8ed9-a8f86310e919	4097ad2b-5cb3-4251-84eb-37d717b34320	25	f	f	\N	829.9465592026584	2025-11-06 17:18:27.303545	f
4206612b-28d8-4a18-ad94-49d47bfc9d6b	a7b61896-15db-43ae-8ed9-a8f86310e919	5c355aa0-2d53-495e-b394-ab4412f80ce1	25	f	f	\N	1772.3943307238874	2025-11-06 17:18:29.537226	f
4a3d9456-9796-41d8-87ad-b8573511992c	a7b61896-15db-43ae-8ed9-a8f86310e919	687a5633-0165-416f-9894-7168feb1d267	25	f	f	\N	734.8606875152143	2025-11-06 17:18:25.252179	f
050020cc-7855-40ef-97ae-b4224184208c	a7b61896-15db-43ae-8ed9-a8f86310e919	ab7321dd-fad2-4e4e-ad9c-287f4b8f2dea	25	f	f	\N	941.2172537336415	2025-11-06 17:18:27.760551	f
9e7931db-c6f4-4f96-8210-72e6c3e5711a	a7b61896-15db-43ae-8ed9-a8f86310e919	083ee276-cd5d-4d52-9452-df46f531b8e8	25	f	f	\N	745.4632980700885	2025-11-06 17:18:26.837404	f
93fd581c-2a07-42d7-80dc-213b9305870f	a7b61896-15db-43ae-8ed9-a8f86310e919	197fa640-0c72-4d2f-a172-20de8af78b25	25	f	f	\N	1496.8025703560972	2025-11-06 17:18:28.788473	f
f69c07db-f0bd-41a4-a632-cec5fe7fbad2	a7b61896-15db-43ae-8ed9-a8f86310e919	769b97ef-04ea-493d-8be8-7845e6aab136	25	f	f	\N	1870.1523485207706	2025-11-06 17:18:29.154308	t
9426ef3f-d67a-4183-b9c1-53c833cef720	a7b61896-15db-43ae-8ed9-a8f86310e919	a5b4b438-1385-4ffa-a808-d74056e14064	25	t	f	\N	1171.2097076608802	2025-11-06 17:18:31.048997	f
a8f17af0-7492-4cb4-949c-c9bd1b17f23f	a7b61896-15db-43ae-8ed9-a8f86310e919	fdcd492e-7285-46d1-a883-6cabb69f25bb	25	f	f	\N	1032.1144090322898	2025-11-06 17:18:28.108009	t
8948a883-3d8a-4399-a2af-95bcad07c9f7	74b00cea-b9f0-42e1-840e-fae2979a4d6c	e5d7a119-5901-4832-adb4-7fac9e4690da	25	f	f	\N	1481.6169210470748	2025-11-06 18:07:22.293629	t
37e642d4-9ad7-4c87-8650-a737116b5f0f	74b00cea-b9f0-42e1-840e-fae2979a4d6c	4097ad2b-5cb3-4251-84eb-37d717b34320	25	f	f	\N	829.9465592026584	2025-11-06 18:04:47.519709	f
0dd2d6fa-34bf-4bee-8f45-8b1ffe575679	74b00cea-b9f0-42e1-840e-fae2979a4d6c	35b0a219-6aaa-4903-bb76-24b70bfa2678	25	f	f	\N	4233.77309179304	2025-11-06 18:07:19.694961	f
fa826b7c-dcdd-4bb8-b5ab-6588fe46f4b2	74b00cea-b9f0-42e1-840e-fae2979a4d6c	f87a9b05-97f0-41c6-82c5-f673fcf67fe5	25	f	f	\N	1025.2442218727238	2025-11-06 19:13:12.713084	f
041a78c9-3aab-4a72-a822-362fe60e1903	74b00cea-b9f0-42e1-840e-fae2979a4d6c	687a5633-0165-416f-9894-7168feb1d267	25	f	f	\N	734.8606875152143	2025-11-06 18:04:47.913992	f
3080a6e7-8016-48d7-b138-779618b55dab	74b00cea-b9f0-42e1-840e-fae2979a4d6c	d3f48736-f1ae-440b-8fb6-ca60d9c16f92	25	f	f	\N	2102.506505989653	2025-11-06 18:06:45.692901	t
de42dfa9-0335-4725-9412-752d1fc2a039	74b00cea-b9f0-42e1-840e-fae2979a4d6c	ab7321dd-fad2-4e4e-ad9c-287f4b8f2dea	25	f	f	\N	941.2172537336415	2025-11-06 18:04:48.414169	f
e93f2c00-f0ae-4ba4-9ea9-57ea7f4770ce	74b00cea-b9f0-42e1-840e-fae2979a4d6c	1c2caa0b-f9a7-4950-a4a8-60288994fc3d	25	f	f	\N	789.5357443745233	2025-11-06 18:05:00.286508	f
5da50f2f-c343-4c74-913a-5ccfd6e56b3c	74b00cea-b9f0-42e1-840e-fae2979a4d6c	208f6a72-aa6a-431f-a045-4a46f9462b23	25	f	f	\N	858.1046452663468	2025-11-06 18:05:00.537185	f
183eb2fa-4192-45f5-a817-8ff7f2cb771b	74b00cea-b9f0-42e1-840e-fae2979a4d6c	0e7b81aa-2f47-44e8-82e0-84b9ea58f8b3	25	f	f	\N	1017.9713421702611	2025-11-06 18:07:33.097939	t
e365ab11-cbb5-43a6-a393-5871053b82bc	74b00cea-b9f0-42e1-840e-fae2979a4d6c	ee225874-6f0e-4fe2-9163-e692f05e5937	25	f	f	\N	1556.2022007616445	2025-11-06 18:05:34.422548	t
\.


--
-- Data for Name: fantasy_teams; Type: TABLE DATA; Schema: public; Owner: cricket_admin
--

COPY public.fantasy_teams (id, league_id, user_id, team_name, budget_used, budget_remaining, is_finalized, total_points, rank, created_at, updated_at, transfers_used, extra_transfers_granted) FROM stdin;
74b00cea-b9f0-42e1-840e-fae2979a4d6c	b150cc0a-de62-4def-92a1-91429ad37c90	82d5d8ef-6080-4e79-a48e-5a6383825d33	test	275	225	t	0	1	2025-11-06 18:04:37.925803	2025-11-21 16:49:46.807098	0	1
a7b61896-15db-43ae-8ed9-a8f86310e919	abcdf234-fa73-438a-bfab-cdf180a1d602	82d5d8ef-6080-4e79-a48e-5a6383825d33	testerosa testers	275	225	t	0	2	2025-11-06 16:30:17.164696	2025-11-21 16:49:46.807098	0	0
\.


--
-- Data for Name: leagues; Type: TABLE DATA; Schema: public; Owner: cricket_admin
--

COPY public.leagues (id, season_id, name, description, league_code, squad_size, budget, currency, min_players_per_team, max_players_per_team, require_from_each_team, is_public, max_participants, created_at, updated_at, created_by, transfers_per_season, min_batsmen, min_bowlers, require_wicket_keeper, club_id) FROM stdin;
b150cc0a-de62-4def-92a1-91429ad37c90	380f5bce-e6fc-4e75-947d-617fad9d5ee8	Test League	Test league for validation	5KFFVQ	11	500	EUR	1	2	t	t	100	2025-11-06 07:21:58.490674	2025-11-06 07:21:58.490676	553d301a-c548-429d-8e69-087c399a3361	4	3	3	t	a7a580a7-7d3f-476c-82ea-afa6ae7ee276
abcdf234-fa73-438a-bfab-cdf180a1d602	380f5bce-e6fc-4e75-947d-617fad9d5ee8	Aces test	testy	S4ZBPK	11	500	EUR	1	3	t	f	999	2025-11-06 08:27:08.353931	2025-11-06 15:23:06.028089	68baefba-2fa8-4902-9e29-4a174600b880	4	3	3	t	a7a580a7-7d3f-476c-82ea-afa6ae7ee276
\.


--
-- Data for Name: player_performances; Type: TABLE DATA; Schema: public; Owner: cricket_admin
--

COPY public.player_performances (id, player_id, fantasy_team_id, league_id, round_number, runs, balls_faced, is_out, wickets, overs, runs_conceded, maidens, catches, stumpings, runouts, base_fantasy_points, multiplier_applied, captain_multiplier, final_fantasy_points, is_captain, is_vice_captain, is_wicket_keeper, match_date, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: player_price_history; Type: TABLE DATA; Schema: public; Owner: cricket_admin
--

COPY public.player_price_history (id, player_id, old_value, new_value, change_reason, reason_details, changed_at, changed_by) FROM stdin;
bcd636db-35d8-4753-90cd-97f524637f84	f87a9b05-97f0-41c6-82c5-f673fcf67fe5	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.320333	\N
ef9e30a7-c55a-4d78-b015-218bda1b212f	083ee276-cd5d-4d52-9452-df46f531b8e8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.322476	\N
9d81d38b-68f4-4ce1-afe7-789ac8aba0c6	4097ad2b-5cb3-4251-84eb-37d717b34320	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.324096	\N
82d9ec4a-2a83-4c45-8cab-45c1922f6adb	ab7321dd-fad2-4e4e-ad9c-287f4b8f2dea	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.325807	\N
7a9d706b-711e-42df-a19d-ff1e737261b4	197fa640-0c72-4d2f-a172-20de8af78b25	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.327318	\N
f4e5ca2c-58ea-41f1-b1c1-9ac9926ed9db	687a5633-0165-416f-9894-7168feb1d267	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.328743	\N
18faaacf-a992-4dd1-b70d-00b046f31495	e08a0b13-4bf6-4853-8d72-84273821e0c3	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.330014	\N
289d4df2-07ee-4d1d-a883-c586ebc030ea	fdcd492e-7285-46d1-a883-6cabb69f25bb	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.331159	\N
cc99e2e0-e25d-4b15-9dc9-830890985839	134b2220-525e-47d8-abb6-58cd86018c97	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.332487	\N
30a20a78-3fba-4bb1-95e3-b25a4d6ffd73	769b97ef-04ea-493d-8be8-7845e6aab136	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.333679	\N
bcac8196-8292-48b0-a447-9ed0ee4b10a1	063a8f6a-dda8-48b4-a1c4-af72700dbcf5	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.334769	\N
237e5615-f8b3-4da6-8fb1-4303ded03e20	5c355aa0-2d53-495e-b394-ab4412f80ce1	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.335804	\N
863113bd-116c-4d14-9b77-d39702e6dc65	81a2d3dc-03b8-4335-b999-b3a7a4125248	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.336849	\N
22b8da9a-0cdf-4c14-8496-8f52ec8cc49b	7b44ed37-04c0-44b5-ad45-a7198f6f49fc	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.337883	\N
d13c6bf6-d47c-4433-a55c-04e6864f2ebb	e54276b4-aadb-4a92-ae26-da1dbf1c431a	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.338937	\N
67982d86-3d25-4d28-821a-c83ab3a62131	a0126b2f-d744-42e3-ad7a-a33ee87472aa	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.340086	\N
9afeb946-2407-4736-b0d3-20459adc235d	702a639b-f4df-44a8-8126-1f0df8e609b7	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.341216	\N
f0f1bcf8-bd31-4ca1-bf4d-68b826b56dca	7c8886a4-488c-4ea1-ac8e-e82d7907ca9c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.342639	\N
b3428004-469b-4382-9ed2-bf0ba99284f1	12853a6b-b381-4424-8295-54daf3905cd1	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.343839	\N
8fbdaea6-b4e4-47c5-b5f5-d92524954298	22cd8921-9675-4dab-9711-12b4e2529088	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.344869	\N
a8bf8b7d-7040-4ddc-9b95-9f34f190aab4	3770207e-302d-44cc-8b7f-c8e78330fdaa	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.345983	\N
e13a985e-88b6-44b9-b717-36c8fe331596	87077270-44b0-416d-97d3-dac0ea7ff6bb	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.346954	\N
8c8d0b00-18f6-48e2-949e-601763c453e6	d2072191-5b2f-465c-b96f-08983b09dcc1	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.347926	\N
14fcb64e-2111-42cd-ace2-1717d98b54dd	2ce403ab-50af-4529-9a66-78d21f64fde7	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.348853	\N
67422f12-b81d-41e3-a0bf-c66d296fb1d3	b3274fe1-7f86-4417-be3d-832acafccd3b	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.349804	\N
8343f6cb-c07b-4ac9-9c6d-a7a181b802d5	333348f5-926c-4c79-9121-bd8d91860319	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.350751	\N
9489d4ca-d280-42c3-9775-737646dbe6b9	207953c2-526a-4755-8701-b6fe45556579	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.351674	\N
3fe4a39c-960a-4b48-8932-5e4448fbe2c4	ee225874-6f0e-4fe2-9163-e692f05e5937	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.352612	\N
b6473d8b-5342-4568-92c4-4fec8f4cbcfe	86a2b042-fc2b-4960-a1ac-eec4554c5fb6	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.353584	\N
cb8c46cb-0fed-4ea8-b339-5fa99d674582	a4bccef5-cb34-4f84-99e9-cdcefa970f2b	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.354545	\N
71f7e667-ef73-4459-b740-423235d022d1	baed7f44-2b87-40b2-9304-dcfebb651f36	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.355513	\N
24c26f94-8e6a-46fb-81e4-a6aab70ed23d	51ecccfc-094c-43f6-baee-cec556829beb	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.35665	\N
c00cea42-453e-45b6-8a59-47c6de51fc54	c4e2f69b-3ef4-41d2-aab6-fde59e2a461b	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.357584	\N
917ce4d6-9df2-42cd-8dd2-768f87225f11	26cc3e4a-f04e-4879-9e5c-1c2464611932	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.358674	\N
9bd60bed-b2f4-4607-a5af-43b7f07bf917	e6eca08a-a0b8-410a-a329-58fe36733399	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.359801	\N
02274ea7-213c-403e-a305-dfbdc63c94ec	73252dbc-3c46-4b48-b6c1-9e874f04a865	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.360828	\N
663141e8-2b85-4ee8-a74e-11437b1cffef	1564dcfe-6b5a-4522-b699-ff6c39dfd2e5	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.361774	\N
451abe38-2ca6-47b0-8d80-8e25bc5fbb88	d3f48736-f1ae-440b-8fb6-ca60d9c16f92	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.362681	\N
1c0c1ae0-2c20-4d12-b715-99d20e810733	d0f81038-7c87-4116-b3de-508c210b6559	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.363584	\N
bc2d6544-9d00-4e21-aab6-e355773c4a51	5efdc5f2-3927-4d82-a05e-76cf7f08c317	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.364505	\N
7ed0655a-b1e3-40bf-a0ac-546c8e91f111	2559e411-7604-42fb-b602-132767ed8f92	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.365406	\N
67f77cab-ad9a-457d-b464-1923f00b07ea	bfb30809-f824-4aa4-a416-0ee72f236009	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.366368	\N
1a98c8a7-67a1-4865-a09a-0ce2ee0fcd7e	5028f8a4-0e0b-467e-8909-dff01013a9b0	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.367338	\N
f6179112-0844-43cf-8f47-4a287f6bc845	301a8d5a-bb31-4112-b1f1-7675da44c1e5	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.368298	\N
bd3fab12-ea5c-4eef-b59f-f721dcbda5c7	b54db491-ce1b-4159-8a6b-bf16635de255	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.369391	\N
0730a5b8-51ba-4d87-a731-13efccf40fd4	eafc47f0-50f9-40e9-af3e-b9fbd8b24d75	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.370368	\N
88d0b246-1acd-4313-ae6c-e2f1014d78bd	4b3b6a07-1631-421e-a3e3-9beb9f8c7624	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.371331	\N
74998d4a-99f1-465a-949a-06da655c29af	01022fb5-a396-495c-a680-63c172b2a840	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.372266	\N
96b0b3da-7c0e-45d7-b168-12097381d59c	31ca0c0e-315e-4346-96d2-a2a2c00032f2	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.3734	\N
fb438406-be49-4aae-b6fe-2225750cbae7	20c3ebc6-b60d-4bd1-99bb-c912ed5b5db1	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.374507	\N
fa280dbf-ba94-47a5-8ecf-002155705bb2	6be9f920-082e-4c59-bef1-799258121e16	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.375801	\N
f11656d1-acb9-4dc2-bedc-92f393954a4b	1e6b8c8c-d6ca-4095-996c-1d7c959b53d3	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.378122	\N
9c023cb4-f3f6-4a73-9c50-e71409c515a9	38e881f7-a5ca-4be0-b29c-27c0aebef1c6	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.379147	\N
5ab2294a-d9ea-4334-8395-080264ea6ae9	f34a7040-63a4-4e06-9ec1-cefdf89f5086	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.380098	\N
bbc6382f-5fe3-4531-9e5a-bccd46bf0381	16dc2133-c16c-415d-bfc6-b629e957e9fe	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.38104	\N
96729ed5-b436-47d1-bfd6-f78d0abf0db3	e202b57a-e156-4bc4-a4d3-a6fe53b0182f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.381931	\N
1be77040-9b3f-4f8d-a3d0-3ef2573aa3b4	cac2cfd6-d5a6-4e6f-9bc1-d0b99d181320	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.382824	\N
ba1da624-6e42-47af-8077-fb5837c7349c	9b9b3697-9bd3-4204-a26f-51abeb1ef979	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.383742	\N
e660e91d-8d10-4599-b3e8-be693ce7e8b4	1b6f3ee8-3777-4a5f-a2eb-8fe91af4b15f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.384629	\N
ffc89495-0e1d-4d19-a20d-3c2a5aceb250	8e02b6ae-3692-42e7-a63f-4a08551fa9ef	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.385512	\N
bc93b004-d5b0-48b4-9ba6-8c1072108a8d	1cbf5983-b806-4bc9-b8ff-04226fa78478	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.386415	\N
646cfb5c-b1d3-4bf3-8221-cc13af438960	5a8d0654-4acd-4f23-9ed0-c7fcbadd04a8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.387293	\N
8a3d74af-5928-48ff-9942-4f9dfa16c0e8	ca482983-b014-4f20-9ac4-218d9193aed5	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.388219	\N
e21ee9c7-b718-4cec-ac77-ed5ee96f868c	299c3464-0350-4493-89b4-ad8fd31112fb	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.389092	\N
2676a592-7685-4620-9fe5-6d3bd1982c57	208f6a72-aa6a-431f-a045-4a46f9462b23	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.390037	\N
aeb615c8-5d65-473f-abe0-99c8cc605ac2	11aa9544-ea4e-468a-ae52-5b4397f2a852	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.391075	\N
3f5c4769-cbac-42b2-8ea0-6f8e4209f9c2	bbe1942d-4565-4594-959e-8a6d217b6d70	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.392186	\N
d1cb2548-388c-4ff9-9a5a-4a7bcf13c7ce	49c2ff3d-1f59-4058-ac8e-28d55c5c0095	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.393323	\N
b2d35cf1-b15e-4a56-99b7-59c7e1dda2a2	dc21bec6-540e-40c4-b999-13a1ef94d311	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.394256	\N
99ef0797-7ef5-4a6c-942e-e00e6412bb0b	9d9e3c4f-ea3f-4350-89d4-ff2c912c00f7	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.395178	\N
ee2ed534-91ed-48dc-be34-3b086ef210ca	4539e023-4fa2-449d-8e0f-b61e5222ba07	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.396154	\N
0cbac488-2e57-4935-9631-fd2f22cbd886	d7460b50-c8b2-40f7-8983-662c4c14146d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.397114	\N
f9d4fc3e-59ff-4cc9-8e60-f1517b8f717e	a7a3f602-01ee-4a75-ad0a-9e6274c1693f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.398081	\N
27ceed91-1337-4d46-bc23-b78f583ed54f	ae7eaa9d-5d87-4968-827b-e0b3cf666ff5	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.398995	\N
a47e307c-88f8-4be3-adf8-6510cc061069	e9b86a07-574e-4d63-b226-8b5e060d109d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.399884	\N
56de2fc4-6e76-456f-8aff-4a4342b50794	3e17c600-2d6a-4f62-9bcf-7f5ecd24d93d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.400807	\N
a9c415fc-4664-4aea-ba6e-4199af71e8f9	ed0c44b5-47bc-458d-b05c-e85eadca8e81	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.401708	\N
82d1c16c-bd05-4237-9e98-687ebfe6ebfd	f845740c-5518-4b81-8c0a-ccbc2c41bc6a	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.402594	\N
7387b2da-dcdc-4fe0-ba28-f438de69d288	dda46009-8890-4755-aac0-9ec325805855	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.403504	\N
2fee2986-1da6-4946-a437-42f577ab98fb	5aafd0c8-8ab3-4df5-ac39-014e239f6e6c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.404385	\N
5f664ff3-c5a1-48c5-b31a-1cba92232428	42c18fe4-ea1c-4bb6-a04f-0504657d557b	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.405253	\N
2b6a7f34-90b0-4821-8948-1fc20a4d416e	8b27a7f2-e91a-43b0-be99-0350b2cce140	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.406122	\N
db6f7f1b-34d7-4aba-8b2a-ac483f1290de	067991da-7190-470a-a08f-ddfa25ef36a5	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.407004	\N
9ef1dead-2950-4329-9c9a-34f6288ec58d	e20f4d9d-39c4-4e82-8fc8-adf6f56aac0c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.407907	\N
1f7da521-af35-49f4-ad23-01d0cc899800	0b8537eb-86ba-490f-a11a-4962d0e794f8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.408811	\N
15b3dfd8-47c0-41dc-ba5a-5c846f2ebc0f	6e9a7550-6951-461e-ae7c-cff8cdd8ddb8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.40969	\N
39124525-ae88-4700-83af-4ae8aeed4a22	4f8cd1c9-e6bf-43a4-a5be-a3f622be363c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.410591	\N
337347b0-6086-4942-9bc7-1e640cc3927c	835c9513-385c-432a-89fd-36237ec0c0f5	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.411569	\N
1e66bdf6-2692-4444-b614-e5e91ff48dd3	27fa5307-412a-46fa-b380-5f01004f58e7	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.412532	\N
a89fb6b5-3b60-4298-89e1-33754b678e44	f98f9025-066d-4192-aa22-0408dc428c20	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.413523	\N
5151824e-3e33-40a4-8902-f7c921b7bd30	9c012e99-bde6-4e7c-8b2e-40411c6c6c24	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.414502	\N
97088c6a-139c-4d15-b833-16ef27d04aaf	1c71fe37-c931-4bcb-88d1-8679e22b01ba	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.415719	\N
70397954-dc2c-4d97-b9cd-8916108fb908	b3092d39-00c9-4f56-b3c6-172d1523fdcc	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.416766	\N
24a00171-5873-43a4-9f37-0985be1edcee	b0b4b59c-4654-49df-8cc7-d5873f490dc8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.417749	\N
7e2b6b4e-0359-4c0a-a44c-5e31e4245f51	fc677fbf-5218-42fb-8320-8d6c4f1b8c2e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.418672	\N
ce3be503-783b-4cf3-841e-1d28d495a009	1fa421bc-f876-466c-9e39-966932c45c94	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.419665	\N
1dc2b4bf-81c8-448f-8ee7-c22b3466ce26	afeeeee2-d197-4a94-982e-3efeb2a29143	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.420595	\N
7da08418-ba33-46c6-a6c2-d8e2f946f89e	2d0b5169-8ef7-49be-bf2d-fe63a5049634	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.421491	\N
c8091f3d-98a8-4189-830c-280d3eac6cc2	fe436d8c-b5c7-4037-97b2-77862ce6d755	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.422381	\N
64d76297-55b7-48d3-959b-c183e8db7f3c	75256ddb-be5b-4028-ad25-4bd67ea686b0	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.423385	\N
4d0cf513-092d-4721-9a23-b86e237d5097	3f75101c-a5e7-48c9-8682-4ed3ae772ac1	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.424408	\N
0d3f862c-ebec-42d1-b6c8-2f75d94a744f	ddc39f03-d0ca-4c0d-ac9c-d68a336ec99f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.425453	\N
a83e93b9-9e14-4318-aad6-cb6fed7b44c4	919256c1-4987-4216-9fa8-b100875cefde	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.426491	\N
5036f6fe-ba3e-4d77-9869-7638b996cc2e	476ac7bc-f136-4bc4-bd9a-95b3ac4e3be8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.427556	\N
bec65588-a0fd-4bbc-8613-ceacef655cff	12c69d23-9759-4a41-9195-f15bb384083e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.428677	\N
a64d0377-4040-4d8d-9f6b-fcb3f946102a	9f6f64c8-e751-4686-b707-79a3de809966	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.430213	\N
f2e1b2d0-59a9-4bda-a419-0914fa5059a1	3197ac32-9321-4007-936c-f43849bcf8ba	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.431563	\N
504b6a3d-98af-44bb-aaf2-ac05addcdcaa	ac257ee0-1945-4b05-a3b2-cd0dc1bfb9a3	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.43254	\N
f6524976-8196-4d98-88b8-07029adb25ce	b2891ab9-f95a-4c40-a991-f6fdac5560da	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.433502	\N
7a272af5-bf2e-4623-a02a-a3c020c67f5f	2e5fdd40-c250-4aa0-b74e-4c4962e72954	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.434388	\N
1c87c7b5-31fd-4c9d-9754-a82fd969919e	2b07ffa7-fdec-42da-8995-ff57965dbd84	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.435282	\N
7002ff81-db61-470b-b0b9-53bd05b6993a	bf4aa208-5791-477a-82c1-012123f53380	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.436213	\N
c57c8557-cbf8-4f07-afde-1cd6c80e265e	1c2caa0b-f9a7-4950-a4a8-60288994fc3d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.437166	\N
9e92cdfb-244d-45f9-8f93-6849eff39188	5b33fcf3-7d30-4b2d-b203-9d24eb2d4c7e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.43808	\N
80a2363b-4e1d-4dbd-a81d-8a10efc5ea65	dd4ca219-92e5-462c-933f-6433959b4bbd	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.439015	\N
e10c5d9a-1870-4bd9-86a7-f8919e1b2d2a	f5f7c630-eaaf-46dd-85e5-2cacc97a996b	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.440116	\N
d1198c72-9e15-4389-9aaf-5877a24d7294	da36080d-5101-4a5d-b0ef-856cb24044e6	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.441251	\N
5a49e5cb-7d6f-4b29-874c-f4ee06cab093	dfca9b5a-eac3-4bfc-b8fb-cf874d1f6d84	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.442287	\N
207bd169-ee0d-400b-999e-31dcd08b829c	0c8c23b4-a9b5-467c-93b2-1f8813eadf47	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.443481	\N
ba66bf5d-4e83-4e9a-bcc7-9fdc80573f3b	0385f0dc-f7a1-40b7-aa5f-ecb3078408e7	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.444702	\N
11902c48-4cc2-4b0e-86f3-863162f3bba5	132d0dce-6d56-4a5c-8fa9-58f7ea63f16c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.445705	\N
18a62a6e-4bb3-4b19-b7c6-bc7fd0c0bb61	3b38711c-99e4-4c16-8488-8be214b9ddbf	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.446634	\N
1a10de38-5b91-42a4-ab72-b90110237035	b7e0e8ee-8f9b-4173-9df0-caa83571c6d4	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.447548	\N
2d556ff4-b2a0-4911-80fc-568e47b6a676	2a0b386d-0d09-41c2-b73f-eb8cb8ec95e4	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.4493	\N
eec60eac-b333-4729-a93d-571bdf2b0909	a39d0cb3-90bb-4423-a005-ec71593448df	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.450267	\N
3a46ac18-d165-4f37-8fa3-8af244afd339	eeaf814f-2746-4830-969f-21fb21bf79df	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.451279	\N
8a8b9a42-c5d7-4c1d-b2f6-2819ea3d51d3	b4de57cc-bef6-41ec-bf5d-84032872e710	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.452224	\N
8230daf1-6c54-42a7-b18f-6b8cb2f9d91e	6bb35e30-7bcc-431d-96a8-2f4f104ce7d2	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.453128	\N
d60438e0-82d3-49f8-987e-49607ce7fa72	6bec67af-c6b2-4aac-a8bc-0913d1b165a8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.454029	\N
a202b444-437e-4fea-9f8b-f1b8e1039d71	656dddb8-b9af-44eb-9cc2-7388d71f966b	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.454917	\N
118dca29-a4c4-4a21-9f43-c10c3cff96cd	b61c8da1-b6ad-48ee-9ba1-712bdbb13883	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.45582	\N
f07d3d0b-3a67-45b5-89e0-7e60aa106c2b	94a71488-a08c-46a5-8ff0-07e2c7b65123	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.456705	\N
28a6f7c1-139a-4cc2-8eeb-efdee93a1e3f	a5b4b438-1385-4ffa-a808-d74056e14064	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.457581	\N
6ee2ad36-858a-4feb-ad38-551b53c6eab5	15e000ff-0164-4a3d-adbb-247e94b9512f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.458482	\N
43bd5b78-4ff9-4afc-8105-f78a44f039a1	ee3fbb3b-1324-402d-a12b-58e3b8274229	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.45937	\N
d0f54316-17ab-4a05-bb5e-25e1e2bed428	48700242-ad94-45b8-a9cf-5ff1402ab9de	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.460258	\N
f2ecbdb6-ce50-4ac4-902e-5f3cca63b06f	e2467f93-bc90-4426-9a26-a9a26a128a34	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.461402	\N
4fcf736c-c3e3-4db3-be55-70f50dac4ac1	4c4152c5-9069-4078-ad38-46aa38bc91bf	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.462324	\N
31fc160b-d5c3-43a4-bbff-0f645be63bdb	9fd480cc-4434-4fba-a213-e5ecf54eac30	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.463226	\N
b54b9491-49a7-4f96-bda5-d3f93baa2ce1	5fcb6e12-6c8d-4e69-974e-21a2a765bdfe	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.464127	\N
6c548c15-5f6b-426e-bf51-449cc0fd70f9	4da27741-4e56-4573-b68b-5ef610228e24	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.464924	\N
8741837c-e576-42aa-915d-cd2127919884	e4ea05c6-ca6e-4c40-8a39-0c2d363e868d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.465694	\N
b7d4c893-51db-4857-a6c2-4ac8684b6712	4a98a7d1-09c1-4e21-a565-7138c0c25ee0	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.466545	\N
600835b0-1853-4aef-acfd-940fe9e4fcc9	34fb5bc5-3efe-490e-a382-443e8b132cb8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.467331	\N
3213f855-8d1a-49e5-9388-5677e2143c8f	4f6a2f8f-0e26-41f2-aed4-71de6d654c5e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.468121	\N
5895ccb2-e490-49b7-bf31-a1801e74ae9f	1bbf21b6-da24-4b08-9b2d-81b635f51fb4	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.469008	\N
890703aa-7082-47e1-9d5e-9729cda133f6	8b011044-6f70-4d49-8e8e-b19d40db1303	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.46991	\N
64eb2397-2836-4708-8435-06e5b3076340	9c1a5c81-1137-4ec4-b232-a9c2cddeb82e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.470771	\N
6b28bdd7-d10c-45b3-b49b-8f272cf829d8	deb5cf75-a953-4507-96c5-ab68dedcbd90	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.471692	\N
c4e50eb4-1f05-4100-af44-7077dfda82f2	180b9284-2aa9-4b36-a9a1-e82dc089ca73	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.4741	\N
8828a5cd-0a08-4beb-9335-a5e3564a41e0	fe0a10d4-deba-4cf1-8db4-7f4df28924b2	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.476574	\N
b8c58677-eea9-4ff2-9aba-a509a7a11772	cb7a4acf-14b0-471e-8820-48a144e9daa4	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.479559	\N
f887f0b9-f13d-4c19-8242-20c403b83035	b9f110ed-2902-43bf-8765-67cc822c24f8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.481504	\N
434df6ff-a35d-4906-9c91-c56dd6e0be6d	63b0dd2b-b44d-42b3-b2e7-a7fd9c79cc6f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.482891	\N
2ba7471f-ecaf-481e-9746-74a5ffcc4b68	265f355b-b504-4857-afc5-893ec78e6936	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.484002	\N
60a0ab89-28f1-4eff-af4f-85eae637a4da	8c3cfa94-44cf-48ff-a9bd-b78690bd95c1	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.485232	\N
6c3cd58a-1881-4bfa-a02c-bc700f6f2d4b	97cd14e3-c10a-4290-926a-fc2f536eba90	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.486629	\N
3898cb61-5380-4787-8ce5-57b0919c5b9c	8109c37b-da04-4339-a0c2-4653c04a735d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.487862	\N
90f60ecd-5229-4ad1-81d4-579fff426099	e269179a-3b93-4e4d-89cd-0cd4e8e8193d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.488765	\N
343b2e8b-cf43-43d0-8677-24411ca58454	be74d414-4918-4d6c-b188-1e952ce3ea77	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.489544	\N
a4a692eb-0cbb-4df0-89ad-ff0a3b982325	33aafe40-9ecf-407a-ac21-8d6184c28d15	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.49035	\N
33dcb00b-3172-4d1c-b183-37151a1a3996	b2f51ee4-6716-4a03-abb5-a9ed86df2c94	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.491187	\N
2e19f722-8782-4e9b-888f-9e6d062ab58f	6b3ebf6c-a8b2-4008-86b5-0e576a8430e0	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.492064	\N
91206ecc-e688-43ed-85a2-b9b308d78141	a91b184a-1909-4579-921f-470855feee3e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.49299	\N
544a323b-bf50-406f-9464-9b208df5fd73	b44d4ff3-0285-4638-bfd7-c8b2f46c0e97	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.493903	\N
60828040-2ef6-43b7-be53-def60668afb3	ff4e5782-4934-47f3-8cae-548848ba7f11	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.494774	\N
c043b5cb-9a9c-4e48-a621-92b749d42f2a	239fb51b-611d-4bae-9bab-5d05f2ae0b62	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.495729	\N
d54db895-9909-4ccb-919f-7cc968e8fcfb	afd0f2d0-30d5-401f-b452-5c2decf8ed4a	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.496605	\N
8165e0e7-8057-4e32-a5f1-f07cc83bdb8a	dd1a0b5d-49ed-4fa2-b159-1106e07058cf	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.497489	\N
312b9eb8-d27f-49ee-bebf-e68d74febbb0	e55f45c6-b6e1-421c-967a-c9ed50af23e5	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.498381	\N
6d76548c-406c-4384-87e2-2811c929de0c	5fed357e-f8ee-415a-bf3f-bcdb18276761	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.499268	\N
4ba05b52-6443-4f30-abd1-05bfbd6a85e5	9e2ecbcd-8356-49a9-a6be-dd52a92d31ec	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.500168	\N
cb224177-5dc6-4d19-b236-2bd0766544fc	b8cabe1b-5d0d-47e7-aa69-37b8b561094e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.50106	\N
29ae3170-524d-4c93-b420-c51d708b218a	e1f526dc-b2a1-42cc-97ce-2ed7006be71a	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.502003	\N
91a1c549-8c33-4a37-b0fe-fd9d45797704	e84013e3-06a1-4959-91f0-1eaba55c329b	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.502943	\N
7fb2eb99-829c-43fb-b78d-39071e0f746b	70452429-73df-4aaf-b89b-0e2f2f27a4bc	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.503804	\N
437a6fbc-0d10-4341-8e90-86f45e4ba6f2	7d24d7e2-845b-498f-a998-67ff746d985d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.504761	\N
233f07f6-4578-4c72-92f9-030eb714470d	ac2f9708-1558-4830-b368-b2e9dc056011	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.505621	\N
3b9d99de-eae0-4962-b330-ffc769a5884a	1757a48d-48cc-4981-b5a1-be2e36ea1f4a	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.506487	\N
36c2d3f5-ff6b-44da-8a1c-132ba988b503	eb8e1486-6485-4353-8ae9-9ddb36c7d924	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.507414	\N
50c76bdd-1482-4bfc-ac7b-33bf20d42bbe	7dbd4577-1a1e-4ac5-89ba-9a4df4b9dac9	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.508358	\N
78fcd3dd-107f-4c3a-88b8-0ef68e21204b	b1f4883e-4fe9-49ce-b49a-6b61f86cb64c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.509267	\N
f37ce44d-0dc4-4dfe-b121-c7b6ce75d78a	d6bcd647-3bfd-4e72-b74f-1ae4a2f2cc18	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.51018	\N
f19c2ed9-5407-4cae-8e5f-64ee26d6bed5	78a55733-4254-4fea-a0c3-106919609fb9	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.511079	\N
aad960e7-f51b-472e-9296-6330eb2bf6de	290e0a56-4f5b-48c5-a696-71d3d36b54af	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.51197	\N
ce58585c-01b1-4fe3-829f-25e245145624	e5d7a119-5901-4832-adb4-7fac9e4690da	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.512868	\N
bbc4e3bb-fd5f-4022-a2e7-c3fc3c26987c	6845e989-bf30-459e-99ac-b6f16cee77bb	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.513759	\N
2af71551-0b29-46ec-8201-f724509e848e	f6456e3c-d439-49f1-92ad-ca1407e80632	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.514658	\N
06bd5570-b653-4b10-893f-5a43a021bc32	9cb710e5-9677-4f82-8d20-e6992e7aa1cd	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.515862	\N
b4f74f37-2c89-48f6-9ee0-d7231563b6b6	95c6375c-3720-4db8-96e8-a941a807ffaf	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.51671	\N
13177532-f240-49ff-9663-7bc3d73ed833	0661de40-7387-4ffe-b371-3bd8cfa34d96	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.517462	\N
0cad3122-a901-4040-96c2-9c68c5d3e4c1	aa4832cd-f0cf-44c1-a9f0-45ebe469ac15	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.51821	\N
45854a82-5fd1-4fd7-97c2-a568bfb121a8	d004c2cc-7812-4f5e-98d3-5bd4538d6752	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.518982	\N
d75c2133-167a-405c-ae7a-5f78be9334f7	0c2802ba-dad1-480f-b834-adc04b2f3ac3	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.519849	\N
495acc25-b649-40bc-9f0c-1ae0bfb46b80	677ec853-a72c-44b0-ac03-d8fb5c431434	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.520758	\N
ef60adcb-1dfd-4749-bf06-d8a2aac03a96	db3d693f-3e13-4b0d-90a6-609219157438	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.521639	\N
c946558a-67f1-45ba-ab86-6c8d4b41fe33	c6c3f386-132c-405f-b087-61d92736ae2c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.522515	\N
fe3c235e-63a3-4cab-9a38-a40e9f274e8a	5dc1fffc-43c2-4342-9f44-c6bf50320bd3	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.523497	\N
3e606f5f-7e53-478b-9ac6-e8d4853558cb	259e50e6-c758-4861-860f-7b667cb84078	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.52446	\N
152aa7c2-7d23-4355-bd36-42576edfd0c8	7382a4cf-1eb7-4458-a7fd-85eb6147c780	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.5254	\N
4d68ab14-de4e-4576-a8dd-cedc01e429a7	4dd10796-86fe-413f-b13b-564f34125d36	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.526332	\N
5c1db0ab-ab4b-45cf-9fb1-8a2c0cf7bab5	a9f9b3c8-2da4-4b37-b032-faeb0d336a90	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.527244	\N
c5ffce92-7c34-4d37-a41e-b26bb548958b	e0dab0c2-2537-4af1-9319-458e89b929a3	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.528142	\N
249c9078-36a9-4f29-917e-5a7d960bb643	37d4e6d7-122b-4992-9dc5-399e775d96d5	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.529043	\N
edded8bf-c465-48dd-a501-5b14edc24277	9a60a4f2-4d70-4429-b361-e1aaeed732b9	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.529939	\N
e01b6801-88d4-4589-a883-2d6b834e8a32	261350c4-3152-4306-b717-7d42cf5b7c28	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.530835	\N
d5bcb5cb-d810-4048-bea6-45f4095ad355	fdc1ca7b-c1f7-4739-90ec-719a5b0d4276	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.531884	\N
4bc328f5-357d-40ba-824f-3de469766359	2bccfd8a-fc68-4093-8493-cfb83321b895	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.532858	\N
6e862856-b175-44f2-84d1-b995f06ab0a1	b5e8c1d8-7ff6-4d00-9a10-e3050823c66f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.534093	\N
313c5668-3925-4a37-8007-5e4e6fc34e30	9c271ad7-1213-4a09-ab80-4bb0741a7cff	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.535323	\N
25077d1c-b510-417f-bd3d-a20e9f50c814	924b4ed9-f850-46bc-8db6-c4b27a6c3bd3	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.536251	\N
8514ac2a-e909-48c5-b9aa-9172d418f343	c18eaa7a-7249-493f-8dee-82971a27a7f2	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.537161	\N
a0906b96-b88c-4e80-a036-1b32d6eafd53	cc3435a4-0db5-4fed-8fab-d235f2e59e0c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.53807	\N
7cfb8f5e-feb8-47c3-bd07-e1c7bc8d1648	7c524c64-3d16-4f7e-a843-6303d2cb2211	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.538957	\N
fa104ed8-8d22-4c89-9ea4-bcbfb4476584	3ff19e3f-dbb4-4227-a578-9dd0b39dadfe	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.539855	\N
0b82ecb0-2378-4b36-8ee2-a88e854a54d3	47d755c2-3fe3-4d0f-9ecf-6e0e278b6da1	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.541035	\N
f3090b97-ae6d-4fa9-b7b2-8b2485978674	6f2d890c-d68b-4242-ae74-91674477e360	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.542215	\N
11bec640-b080-4898-9776-a100357a6476	6f4b1980-c138-489b-8735-8e5f2bd6aad0	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.543228	\N
40c377a8-d1b3-4e70-87a7-b3d7f18387dd	4a1edcfc-4dc6-477a-b55f-565e397ac9a6	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.545088	\N
0fc79733-7b81-47af-bec2-d05170dd04ed	c720b315-fc3d-4918-ba2f-8cf99f1923ac	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.545988	\N
2c8b81ca-da27-45e7-90af-7f07d97a4389	398e41b4-a2d6-4faf-a80a-02c32bbd0520	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.546884	\N
ba59c084-b35a-4f0a-867e-c3471e074f3b	04761f4e-d407-42e4-931b-a3933ec753f0	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.547932	\N
a4128a95-ec80-46ff-a807-2edf1df564d2	a0d25045-522c-4c5e-917b-b810521b01ec	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.548911	\N
dc147a9c-5547-4755-a320-c40d164802f2	eb75d0a0-8eef-4790-8f50-d7172155e862	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.54984	\N
360eb709-9eaf-4867-ada5-f00917b1df5e	f5cd4aac-66fa-4730-aff0-96ca3fcf5d6e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.550754	\N
797dd2d9-1e98-4625-97bb-3840db4a5cb0	623846b7-500a-42e6-b411-1210f30ff888	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.551658	\N
83825467-f4f5-482e-a6a5-9be99c8a064b	a130146d-439c-4474-9a42-9fcd937a58aa	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.554401	\N
92b84a6c-f099-4ab2-ac9b-af1ecfdd56d4	a4b0c8b5-a71b-40f9-91e2-9fe26075dd11	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.555328	\N
d3ca85e8-47ce-46ab-94ee-c63bffd2fcdf	a3e2e08d-8bd1-4776-991a-c213c025d118	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.55624	\N
4ce7f333-f953-4b2e-8241-fb4bfea14f80	8e05d4e1-18d0-4272-b0af-d23de8c19449	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.558929	\N
60083179-749c-4715-9da6-673a8e4af9ad	0e7b81aa-2f47-44e8-82e0-84b9ea58f8b3	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.561656	\N
801cc023-671d-459f-a67a-3faf1c3af5d1	490a1b6f-4b91-4ce7-8faf-0e003d5f8e42	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.562523	\N
b17534c2-4afb-4bd3-9a2c-efefed2788b4	7852d4c0-9b02-42ce-88b8-86fddfdc1787	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.564304	\N
0a5f54be-df09-460d-a4fb-3a739aa28699	abe9d8e5-fa60-41d9-946f-3baaf6e96d4e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.56699	\N
ec7ec3c0-92f0-447b-a6b2-7affbb6b0592	c33a0794-a4bc-43a7-a6ec-7f22d40c61dc	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.569562	\N
ac5fffdd-7f5a-4c9e-b948-52f2bbf89662	f79f5de8-5f43-4268-b6cd-eb9ac747997d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.570456	\N
470e5e15-f9b4-4ab9-9b92-d3b8fcf0bd90	880a76e3-5423-4ca3-a754-d1263af3df76	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.571347	\N
f2270f09-ef1f-445b-9c46-fe8b38811a35	ea96f3c4-e1a0-4577-8165-4382e73a8c6e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.572244	\N
ff7bdc99-d6bb-40f5-a154-c8f9e7bf820e	7c619bd1-a6ef-4596-812f-c49f81037b42	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.573127	\N
7ec0cd0b-c06d-43ac-a199-d59357943b54	ee32a692-e443-4cd4-b8eb-6759ee91e383	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.574052	\N
ba741f8e-9398-4c39-9cd6-8597f12c3347	846a8ea8-d9d9-4865-8e6a-0bf3a7c64f78	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.578769	\N
aac90099-5114-4a96-bb5c-3f121b84ecb3	1fe65eae-61b5-4649-98b7-31f27bfe7588	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.579709	\N
5dfe59bb-2b86-41cd-880b-8805ea313930	6f145921-b11e-49a3-9154-2050208a689b	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.580637	\N
589c7785-da21-4c13-bcf0-79b95edb2f00	ba13c44b-6f7d-4519-b796-accfde5c76a3	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.582444	\N
02c32f95-a29f-4193-8ab4-e2067b53a9fd	0b55cf2f-3083-4f7d-b54a-a4955390ffe1	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.584274	\N
5180323e-06fe-4ddf-b623-e6c8b799d01f	df09ab42-49d9-4656-aa9b-cbf35fb6ecad	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.586135	\N
6f8815ee-2ede-4941-8184-d202db1b30ca	c5d231cc-422c-4d83-adc3-9b9e7b8c1052	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.587941	\N
6a690700-97e5-4bfa-bd66-c72537036c04	592c3ba3-c7fb-4194-82f0-35817714cf4c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.588833	\N
20f8cde6-dbb9-497b-8bb4-50232d9a1531	a8ab73d1-3b71-4a81-b823-5036878eb922	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.589717	\N
25f172ec-4bd4-4027-b955-00dda5774561	177ce35d-4c34-4c79-b6a7-265e69604405	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.592436	\N
754aa8da-cdb7-4af7-9211-507e4be396af	a626543e-a37a-4607-9cc9-4dd5a11e63f1	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.593351	\N
3ba619d9-7284-42fb-92bd-c3a8d1248582	f217413c-ae14-47f0-9196-582642ab5c08	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.594257	\N
11cd7268-ac3c-4cec-8b6d-84a2815f10f8	a210fd9b-6f85-4ec2-8de7-595cc39415a1	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.595164	\N
95cf7d76-b0f5-4558-837f-029f2e4ae3c6	2b178f36-ddee-44e5-b415-798eff08671d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.596049	\N
c5d2baf6-2220-46be-a3a7-9373606d9ffc	650ed5fd-ee5a-4a31-8fae-8e4079ff6d81	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.59695	\N
9a0bec04-07d9-4c1c-97e4-511eaff28880	522fd27e-0e32-4161-a1d4-65cb89751d93	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.59791	\N
7b5c6616-4698-4467-ab1b-69f3f02598eb	611636f7-2f36-41ea-a672-1afbb5e6ae3c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.600635	\N
c563d932-188f-4226-91dc-395c462a1e68	a6ba9df7-3a6d-4e1e-89da-9d0af7b34c69	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.601525	\N
886705e8-bc6c-4f1f-96d6-dfbce19c69de	a10e7473-c6d6-43d3-a6a5-688cbf08c97b	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.60242	\N
9307a75d-89f5-456f-9e32-68cde043b6bb	2f5310d1-ea74-4fcf-97af-ad5b7fbac78d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.6033	\N
d4844d80-0bf3-4ff3-b596-c9d2f8e43154	111d39ff-a245-4caf-b466-0dbfd7a31924	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.604217	\N
7e324289-ce26-4683-8e3c-f6f46b2c4eb4	f77f7841-d346-43e3-823e-2fbc2376282c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.605135	\N
73514315-65de-4159-8374-dface824c711	55bdde68-6553-4525-958f-ae86b49c3858	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.606019	\N
0ca8acd5-3bd0-42ef-a248-0ead5ae4861d	1f2e7f75-c1a3-43d7-b6fd-153350e4265b	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.606912	\N
5c6bddf6-07cc-49e9-9d93-25125a5df3c3	5707d16c-4335-496d-a081-0278874c6434	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.607796	\N
6b6d0ed3-6452-4c55-a4ec-f9720aec75ea	54c78cac-3282-4f65-a678-6b7a61ee83ac	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.608738	\N
ff039f12-ddb9-45d5-a49d-72f0246a0c99	08e56cfd-3a76-4814-8911-2e08e1e3f60c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.609644	\N
0a686f37-89be-40c8-aa27-42f26fff75a6	bf15117a-15e9-47a9-baf0-227e9d4e9db3	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.610984	\N
f7025e23-91ef-4d32-9ba5-579075c60a32	6c55fc42-5141-4c64-8812-ec7413ef41f2	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.611893	\N
e013886a-29f2-4510-a902-4f46e772539e	a17d53dd-bc84-40f4-965a-bda3e5d2fac6	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.612774	\N
2b172172-bbbf-4ace-9fa6-a25fec8338b1	ac6752b5-7e16-456f-b87c-1f4dcf423be0	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.613663	\N
9e374ca8-8a40-4e38-9996-39beb290c9a7	1ff50c17-6c45-42fd-9e01-01f970a43a46	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.614539	\N
b13de6d9-1763-40b3-ae8a-ae28e95fc407	83418825-ada3-469b-976b-2eb320fbe0e3	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.616105	\N
f6f40730-8e42-4c1c-92e7-d6fab0cf48af	7f278ae2-b4ed-40b8-86fc-d59ad476efe5	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.616844	\N
6fcc80ff-550d-4503-94b0-2b3cae87967d	8cd84df7-ac4c-41a3-b6bf-3bdcb69d3eff	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.617571	\N
d28110fd-e8cf-4691-bde3-2ed854eb4a81	c1d51fc1-766e-4f1a-a03c-2f7a61b64243	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.618398	\N
e6a6f2d7-5a98-42d1-953e-0d05bcdce0b2	8480bbc6-623d-400e-b4d6-6e0665391870	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.61929	\N
53f74d16-6564-47a1-8f27-5bc036205ed5	6728575f-6f71-4475-9d94-553899f6a48d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.620178	\N
8457cf37-e7fa-400a-a4a0-75d34f9f23d9	a13642e3-a680-4225-83ef-d52264f79aef	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.621337	\N
fbc1dff6-4a55-4df0-b04c-74cde0a9618c	75d5b8eb-af70-4d12-9988-6735bb252ace	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.622232	\N
39368985-6d98-43e3-99f3-20a7363b78b1	d6dde139-c658-48b6-9dba-3477802bf55a	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.623021	\N
d0625757-b7f2-4f6c-8328-b7a703b40eae	4a83a744-3307-460f-aa8a-d70f13b34564	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.623774	\N
2f5e03b5-f0ba-44b6-8f01-609830396879	73123f8f-07a5-4b3d-b9bc-6b173b242889	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.62456	\N
0cf4f347-b333-420f-819a-880b1c670e3c	cd381471-5593-4a5d-81fa-943ba68b58a7	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.625334	\N
71d8f62d-674f-4521-a4a9-acdb14fe615f	8ddf3247-e79f-42a0-9ed9-fcd225e8e17c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.626237	\N
44b1c958-0576-45f0-9aa0-b5be15ed70ca	6a400c40-372f-45ad-b2ed-4d18d749e79b	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.626987	\N
ddb0572a-448c-4fab-97b0-16c1626d74fe	d8564052-7605-4751-b09c-682c0370fef2	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.627744	\N
eb333e31-ad27-425f-82ab-31249038cb50	f3faed0b-0f48-471c-b0d5-9efc6300226b	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.628549	\N
b1b119ae-1b9f-419d-a773-9f556e101385	a46309e5-3877-427e-b395-60cb41c3c3b8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.629323	\N
e6d182f6-b370-49e7-babf-4aa12deb2447	8c2eee25-71c5-45c7-92c9-86492e2aaa0f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.630138	\N
dd3b05b7-dd77-4ac7-94d4-9533910c5932	2c967cc2-d539-4e9f-9e61-bdb26721f368	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.631364	\N
2ade773c-49e5-4b65-96ed-645a7544c098	09883877-87ce-4135-a3fc-86ce3a18ba89	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.632334	\N
273ee7e0-cc8a-42ac-aad3-7d7f10de7748	01b0edbc-1255-4834-b8d6-ad3187d147c1	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.633262	\N
f93053f5-4c62-45f2-98a9-d10514248e0e	74b72eb6-780c-474e-ab76-9848e036dfcf	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.63438	\N
4a087fa3-e992-45c0-a3ca-cb07ea48e124	136a5d4a-4904-4756-8ab1-0fcc738ecf38	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.635259	\N
cd5cc861-e08d-47e5-a037-7e02cb687ec1	9584a9cb-81e1-48eb-9165-8ddde91e4484	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.636051	\N
a838e8ff-4505-4e58-9a6d-1eb80219c936	8dc76dd7-9cf4-4054-b230-89e1a162b6d7	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.636919	\N
edbbfe0d-bfb1-4abd-88ce-881e64840b06	4947b901-5b1e-440a-95d8-cfc13387e9ca	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.637681	\N
763bdcf1-bf43-423e-8d47-129a36563e5c	8b8c2e6b-df1b-4f6b-87f6-f135ad274acb	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.638467	\N
9aca3111-0785-4144-8295-f58930b1432f	0cf396df-4bc6-462c-af0f-b3e519b9c354	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.639223	\N
32bd9181-62a9-4f51-8154-72bc3c5195a3	915009dc-e34e-45f9-b64a-e40136f330e1	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.640195	\N
72109c66-8ecc-468b-80f6-c4ff5dcc5f72	6699917a-f50b-4e7a-9fd8-ae590e5f5987	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.641764	\N
7b9b5c79-dccb-4077-9544-6d381053bbf5	81df0839-1701-4af1-b588-6342b92c5377	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.643257	\N
0d75453c-7470-4ea8-9708-6859556b27d2	719f40ed-c22a-4b7f-b9a1-01f106a71251	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.644377	\N
9b67487d-4d7d-47e6-ad73-782aa02fca1e	0b0b3062-599f-4029-a129-ea0428a838ef	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.645542	\N
05fcc342-18fb-423e-8252-8ca6a354c424	44b0ce31-547d-480b-89b3-05cabb660912	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.646398	\N
ae556025-6074-4a6e-a68e-a755998a4e90	84745bb2-dc74-4929-85da-a2353b8b6e82	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.647323	\N
af09fe5c-548b-4c67-aa71-60512efb2346	0b3f5846-77a6-4c66-bfdb-59a38242659e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.648123	\N
678ea777-4955-459e-a414-537a96d10628	1eebe7f5-e124-4b9e-affd-553fe02a510d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.648935	\N
2cce49ba-8f46-4488-adac-0b773d909838	d84e5acc-d9cd-486a-8899-d2fd0e2f2ef6	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.649708	\N
94e40acc-1f9d-44b3-87ed-e1fa0dd775e5	02d08e45-b0be-47a4-b421-06ec39492262	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.650471	\N
7484afa8-77c4-4551-abb2-fad73d0463ce	7bd6dec6-72fa-46b8-8770-9d2443057af3	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.651225	\N
8625fa67-01d2-4a29-a1ff-8d14e9500b1f	e2125da8-923e-415d-8631-3d079bd6b5af	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.652035	\N
418b5e37-b8e4-40dd-95e9-a7c2365a0269	8cffcae9-6927-4351-919c-61ebe4f48c6e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.652786	\N
ddb07cc6-47fa-4a01-9ea4-bef9f4064042	06e08974-ea2f-4e58-99a9-e25f97f208f8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.653609	\N
0704a013-1738-47a8-8483-2cb7c7cad243	b71bbb33-6132-4f9e-bc64-e4eec47682e5	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.654968	\N
20b4fff1-d446-4aaf-8226-740bb8126734	974816e4-544b-4d6e-8804-13575b637da2	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.655942	\N
a5fa0073-be8d-4438-aed1-ec3d651fc756	c989d47f-7022-4206-9fef-bbee5c33e546	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.656895	\N
1cb5bc2c-423d-4242-9093-5d868064d684	99eb8d72-f4c4-4d69-afa6-d11263281489	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.658033	\N
f0d33228-8507-4759-be45-027a4d795ed5	0737595b-79c6-4540-be98-cd97c6c536a9	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.658859	\N
07852345-d914-4402-b790-8e603a789999	f87ffe02-8f00-42ac-aa92-ed60afcbd63b	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.659657	\N
4ddca38f-87a1-4191-8b1f-22a93ed398bc	588df776-bcb6-4e7f-8102-6c05d823835f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.66055	\N
622a62e8-8da4-4fb7-9ae4-78853243f11d	460dbb47-603a-4ea5-b0cc-35487f45ec41	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.661328	\N
087d502c-95f7-4aa0-875a-45801daf2713	1f8ecb5d-fbd0-4a9b-bfa7-394fc0363096	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.662159	\N
e719310a-5381-4be5-bf16-93de081a11c0	77f58c5c-8461-4476-81b0-538d4178c6ae	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.663142	\N
e31b8df0-d607-4991-99d4-8d16cc5cb442	92d8948d-d805-4c13-98d8-d561231fcc1a	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.663986	\N
796b45f0-9601-4338-9155-f6fa0160e3a5	84267f45-af5c-4c42-a820-039865e6456f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.664916	\N
b0af21d6-3aac-4a21-800e-d7b0984cd9e7	2641ff16-de10-4600-b491-8f6d23f36a66	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.665791	\N
81ed1166-a401-4d63-a055-ef3f06360810	3cd42d6e-027d-4b3f-bccf-c9939051c66a	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.666729	\N
79b510f3-1b80-43d4-bedf-9441ebc5caae	ab68e642-5b44-45e1-a496-bf5c0c52e442	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.667668	\N
65ffe3d7-bdad-46af-8b68-5ccaa3c0a3bf	1c625beb-5b44-407a-b04b-a405a372bbfb	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.668638	\N
499e2bf4-48a1-4deb-873d-c8b8041b6a76	b7f41f1b-a36f-40fb-a092-ce39edfa2b06	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.669536	\N
c37bff76-bc23-4eec-8800-7339b12a2eef	2c58831b-0786-4c4a-8c06-fae96d9bee40	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.670418	\N
a6a8bd2a-1f7f-46a2-b65b-6e3707748222	65dcc9f6-99a2-4e88-8c6d-cf3e423c49dd	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.671317	\N
09ea6960-5cfc-4404-ad01-9c851d953f2a	fc56c88f-36c4-4ff7-9b98-42c1327a8cff	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.672238	\N
d600087b-dc85-42c7-8b1a-a8f074c559b9	68dbce94-9929-4a0f-887e-bfbd896dc469	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.673142	\N
b6bd9507-4f96-41ef-bbf6-bf6641714693	d4f4adc2-4937-4c20-857f-5b656acd99f2	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.674067	\N
f6e4624c-aeeb-4acf-bc1c-85b86b014acc	ad8f0f7f-4664-4131-8c58-4ba3dd9cacc0	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.67505	\N
a5f5bf2d-611c-43c8-bf33-1213ada074eb	4dc476b8-3c39-4c40-8c51-877bb917c534	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.675975	\N
74fb3f77-98e5-40a9-808d-fe1e21cf1f0b	6a898ee1-c846-471c-b961-45206f71abac	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.676881	\N
afdeb24a-aeb3-4391-b79a-1d8e7170c67d	aadedd0c-2aac-4f3f-a8d3-4bb6ba1c5d6f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.677775	\N
bbf5d42c-2700-4dd0-adb7-002d47f952fd	64f34602-027b-4ec0-9a16-b6a46fb27bb5	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.678708	\N
b50535e2-c291-41c1-bd70-89697ee2a9b8	9e9e4d96-d3f1-4eb8-9d67-7bad1797c23b	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.679895	\N
f4509d01-5a06-4329-ac20-8f896ceac81c	af9292c1-22d9-4451-a894-169d3fe5ec0d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.680831	\N
8b0a2a71-9cf8-4e67-882f-0951a8624558	85b0786d-8c22-4ac3-bf30-99a04e3039e6	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.683519	\N
392599fa-86df-4a9c-a262-3fea169ce226	4a72f0b2-3c80-4826-81da-75902460d73e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.68848	\N
077ea0f4-42e8-4239-86e1-6b4be2707661	e7ab6301-c7af-439f-8b62-4baa67396bf8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.691218	\N
d9bfca20-96bb-4ce6-8be3-bfc3d9faf951	cd828faf-cba5-4099-bc65-af64df655155	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.692514	\N
0c9510ac-2c92-42fd-bd4f-df5d138089cf	077e2e70-b575-4a70-83b0-0c3ab3c695e2	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.693561	\N
96de5eea-65c1-49ab-a6f9-e2e56b0a8c9c	d4c75d73-d025-4bdd-97be-fd959a5ebca5	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.694549	\N
6277dfc3-e87e-4c8b-a366-49944ee94847	02d275c9-1b39-4bca-9f3a-0f71e0fbf41f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.695599	\N
d520ddb1-f957-4f32-8777-f0e984e0630a	53a18614-d323-4161-bcab-b9ca109819a3	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.696577	\N
290297e9-5c9f-4129-a2a3-6a7e4bef3656	2094b356-2b83-4d4a-84ff-b92ce9c0074e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.697552	\N
192caab0-5f74-4291-b8fd-ff72b3fa0ef8	85fc584c-f2a6-470d-8e4b-bdcd013f4ddd	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.698499	\N
681ee29e-987f-41d6-b933-a8b784b1c3dc	be1387b9-77b8-464a-bd52-28dd3d38c2e0	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.699453	\N
362bfef5-a68c-49ad-9aca-6ae905f048f8	66ea5ae2-38ed-4081-b79f-7f8ab6c22b23	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.700498	\N
473114a7-ce18-4c7b-9bb0-531763db3795	8cea4a0a-ae7a-4b63-8138-b9c9becdbfa9	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.701467	\N
ba8c504d-5053-4391-9ee6-7ab7d8975466	3326afa6-9646-426e-b5fe-d12263fbb215	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.702761	\N
572f1424-f2f9-4ae8-a262-3b975045e8b8	e0598344-f940-4230-85b1-1bae8438b0e3	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.703674	\N
88b0ba37-3a1e-4505-a0e0-dfb66aa46563	829ed784-010e-4249-ad6a-452da85367b8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.704606	\N
185d0914-f75e-4e45-b3d0-7a66d9c83bf4	1ab0dd7e-3d26-4f84-908a-90180b249f0b	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.705569	\N
b1a22112-83bc-4583-bfa8-19a972aac722	61682d04-14eb-4e2a-be57-4f8fe18e1f93	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.706476	\N
f9724bfc-f020-4660-bf24-8f94d162f4a8	025c2139-1f9b-4736-bd54-e6d3dc16f20f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.707287	\N
20d5324a-e740-454f-8044-a9d182d1a5f2	9ba67ce8-624e-4aeb-86a7-eaf9742f618d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.708112	\N
4539d1e9-da82-4a81-a425-12c9a1b7fdf3	eb8fe79b-c145-4c02-835d-b2f0cb051973	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.709017	\N
2e05ac00-e2b9-484e-b4fc-bc9cdb878926	45cc83dd-2c67-4780-8c98-6a3abd7f6507	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.709927	\N
49be6bcb-2961-41b4-a2d2-33ce06ae3acc	7f701d77-50ee-4076-9ff0-b88cb72aef37	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.711142	\N
150c7520-a86b-4bd9-9436-d727664bbf7e	ff47b387-b943-4813-9c2c-56b35b85dd98	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.712118	\N
c154f432-bc7f-4b55-a397-8d608ef7f54e	58c99648-813a-4170-8710-6bf65dcffaff	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.713069	\N
f0ad7c98-ae52-4fe0-b384-69236c35e599	3d07f68f-143f-48be-a5fa-084f27e1aa44	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.713887	\N
b61e0fba-1b00-40a0-b1c8-5024c5849c7a	3a9e0fef-f369-43f9-a721-85a043678f51	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.714801	\N
dca95385-6b66-4a50-93d1-7a39ffd99ed0	48b29f32-a13e-4381-b34d-b4146942a972	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.715679	\N
96d52c1a-6f76-4446-ad8c-eff7ff82d182	d51b3edf-36b6-426d-9951-5502531db4b2	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.716553	\N
35ce06ee-e83d-40f1-815c-1488c78d90b0	4ed499a1-a080-4e95-b8c2-5fc1725fe07a	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.717372	\N
a93c4561-ea31-42e2-a085-29d6435621b7	9245c119-3196-42f6-b8f6-db49c8b2c0c4	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.718179	\N
d564b0da-1536-4760-a3a6-5dae41c9652f	f8fda0dd-df20-4a0a-a2bf-5e4229c544d1	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.718991	\N
a9d2bbe1-57ef-469c-809d-b6557c1f0746	fd8a064f-828d-4480-8cf7-8f0005c41fac	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.719933	\N
a8090a86-55f2-401b-a981-3060e0ba9a44	ad5acdcb-f6c9-408c-af7b-2d6eb502dbf3	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.720758	\N
2266a460-f28a-40c4-96f4-6fc63587f70c	1a8cfdb4-dce6-425e-bd94-3b37e7edfb8c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.721941	\N
309dfb84-d5ba-4478-889e-420053f4d172	65cca0ec-d618-4ca5-b2b1-92ca20e9902d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.722837	\N
7fa5e1c2-120d-4647-9ae3-1ea285d7e9ee	0dd09299-c0e4-4576-923f-6b554acb25bc	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.723742	\N
f0a43a64-86d9-45aa-a485-7d62b58ecf42	503b551f-7fa4-4798-bc71-21153f6df024	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.724661	\N
30d2fbb9-c076-4744-8c99-86632d77ae07	fcce9f14-c835-4b93-b35d-480af2ecc11a	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.725609	\N
f38e20e3-74b4-46d1-b864-f7c9860e37df	35b0a219-6aaa-4903-bb76-24b70bfa2678	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.726442	\N
b8266cce-2503-4d0a-9f2b-b42e291ca448	41d83a2a-b52c-4719-879e-c3cb54782b73	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.72737	\N
143cca95-696d-44d2-bbbe-d6d06f16a6f4	9ab0362a-b6c9-4250-bf88-2e050f67648d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.728185	\N
7a1bcb96-8e5a-47d4-a735-e32dc3b684ae	e297ded2-777e-4f62-b2d0-b93ae80e7269	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.728983	\N
4b8bbc6c-414a-4111-a99c-848e9138061e	b2dfa044-3ae1-4790-a8ff-bc5f161370e5	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.729746	\N
48e0b569-4d5b-4530-9262-7d1d7aa79feb	20f79e8f-08ee-4e0f-addb-c50863ff627e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.730491	\N
5cfae7ea-973a-46ce-ab54-413dfe4c2438	c5ba1ad0-473f-4d73-8b9c-8840d26ca2c8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.731301	\N
e051f749-7806-4baa-a80d-4c6c0f65b2ae	0221fac8-2e6c-4bbc-9ea4-0d67ccb75b1f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.732081	\N
64d9385a-068d-4597-8760-9c9f9065548b	b6537d37-fcc2-4246-961d-4b0349feb6e2	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.732949	\N
689023b3-e583-469c-8d82-ea34855f3ec8	fd77b989-4a41-46d3-b1bd-b78d8c74863c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.733899	\N
fec0ad98-0045-4e69-a45c-3b15a191a4ba	a9dd3458-eb63-4688-8820-394c1339c01e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.734797	\N
f46d6138-63bd-4042-9d63-0d020cdecfd6	a6b90d7e-a1a3-4d56-8a33-d80656b3f3b9	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.735752	\N
ff59afc1-6bbf-47b8-aa37-2d5682ae4c02	f95a23ff-f597-4167-b954-01e4ba514b72	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.736678	\N
42c38198-c502-4cd6-8c88-8db9ff46ea72	39fabd28-1713-4a59-8922-04b1ea36a334	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.737613	\N
64e32e5a-e4f4-4b18-90ae-65365f959359	ed4d7980-c2e6-4dfd-b1cf-f1d775674765	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.738542	\N
726df16e-a167-4d55-9a1c-65f0f9663d4d	73ee0023-454f-4360-b626-62bc24dafe34	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.739445	\N
67959cb9-d52b-4011-8cfc-07d5300e528f	f530f943-4335-4fe2-9341-a41e1f00e72f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.740574	\N
4cce21e2-970e-4632-bdfc-f7f0a3925ab6	03b07307-b139-4b3f-8b53-f8eacfc98369	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.741667	\N
8a07fce2-735d-4acc-92f0-79d9c3bbfb95	3657e01f-4766-42fd-9f2f-6667897d3cb5	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.742656	\N
42bcc1fb-2751-4f25-be67-daf6ed764b1e	8ee902d2-ec8a-4e60-8c98-e342c2d80db7	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.743692	\N
0e0cac61-5883-475e-974d-5e5f47f385f8	015e78ca-5800-429c-9dd3-351538bc62e1	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.744685	\N
bcd302be-2922-425f-97ac-12bfe855e6d1	0f5d36e8-35e5-406c-a922-e4404fdb0bf8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.745645	\N
faabc449-607a-44c4-8b18-3e94fedb1cf6	b294e3fa-2b7c-46ec-82ef-20266dcf355f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.746592	\N
cfc9abe9-247a-4b6b-bc73-9c8def3009a8	e278c570-2e76-4b6e-94eb-7d5c09ee0e70	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.747522	\N
acd9d5a9-a6b0-4717-a30f-f3f292ee1de4	06c7b178-37ec-4728-8f18-9bed72282970	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.748436	\N
8e45b40c-e523-455f-b6f0-5f1159b069cc	2fb11813-bd3d-4809-903c-57230560c1de	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.749398	\N
0ca10301-a058-406c-9331-85def0ed33e4	6cdc9cf3-96e6-4824-bb38-461db366ec82	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.750315	\N
6bb2cce1-6173-4fc1-81f8-90334099df99	a4385a7f-331c-4c17-a0c0-c4d2b6b2461e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.751247	\N
5ef95162-85d0-4122-ab83-46ca266bb4b8	6bc6771e-3180-4f47-89d9-d23ddf2c170f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.752171	\N
cae858ef-9e55-45ad-9f47-d6d23bb6e510	be1578f7-33ae-4508-aa38-335b98f70e4a	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.753091	\N
d1c5a3ed-e771-4ebf-be9e-d367db07a8c6	907d8c76-7033-4141-9f49-53ef6a6df0bc	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.754044	\N
ec7c28d1-55b8-4860-92ed-358dd73a2502	13d7b625-f44c-4dbd-9edc-e03caeb11e90	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.754967	\N
c5558906-ae6e-4cb8-9311-b774f5439169	20822aac-2350-4142-88a5-e18a5cfa1612	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.755863	\N
4ef43ef0-b98b-405d-bff6-f42c232dbf35	dceb1157-9081-4b1e-8908-2a86a8a08d09	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.756779	\N
3cbe4b39-1659-4659-a95a-8f7e916a345b	4ef64320-6c27-401b-86da-213b30d58be7	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.757691	\N
1729fbbe-3a51-4172-81b6-b798f38fdc56	41e9b774-6317-456a-b83b-e25674549bae	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.758608	\N
37e0e0c8-613e-4a15-8031-26b7e2b28c06	aecae709-b658-49a9-babe-6dcfc0f1fdb8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.759552	\N
57bd1b64-934a-4c80-9cda-0eb4fc5c80b5	32109804-5ec6-4f40-a311-6afde507223c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.7605	\N
edf97f8a-0535-4a51-9f9a-54ad65dac314	e4f3363a-672c-4cce-8a6a-a2c09ad62c34	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.761412	\N
f38b375c-ce78-4bbc-805c-15eb2d51c901	ff3477e4-cbde-41bc-87f9-d8e0204fa896	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.762326	\N
527a77ae-4248-45d6-a2c8-6fe06df4c17f	5a90d219-0ebd-411b-b1ad-08f3fc85083c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.763252	\N
31dcbf4e-35bc-4d1a-a7aa-46867a196eca	66faae16-ff06-44e0-a691-9b3596ef871d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.764161	\N
6d848d30-0323-41c8-a20e-7a77f59d8231	9d7d0ff6-3af5-4482-a5b4-a9d0e1ba18b9	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.765076	\N
fdce10f9-d708-4e3d-a8be-f9e3b54444ae	60a19728-352b-429c-b734-e6d8fe3e4dab	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.766	\N
974dc06e-66b3-4cd6-bccd-96fb8307a996	c3a698b4-fcbc-477a-b43c-f9eb1a8dfd21	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.766907	\N
8460cf3f-e068-44fa-96de-8cd86a094d58	0c98bd73-1bed-4a9d-b0f9-948e8df45c81	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.767817	\N
01d4463c-1c17-4df4-a6c8-c826e15785b3	693dbd66-ebad-4ee8-bf69-488b8827c5e6	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.768805	\N
127ee457-90e1-4e67-9a90-e50a929736fe	7f273c91-1e7c-49c5-a6a9-da6eda24c9ec	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.769798	\N
1e14e840-9b81-46cf-8fe7-6e9dc601c59c	c904bf4f-908f-448e-a4b7-deac874e32d0	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.770805	\N
43aa64e7-c330-4cbc-a991-c67184439f3c	a14a758b-0753-4101-9cb2-04123def005d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.771918	\N
6c27bd9b-3713-4b7b-a734-85d1e057e14f	249e11e6-df0a-4bab-8697-88494377480e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.772932	\N
136f9b69-a283-43ca-8193-a6eb2782b69c	192315d2-23b8-4668-b978-039183ac0036	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.774416	\N
b1f315dd-55fb-43e3-846f-e8c0e2349154	b4776d46-f3dc-4732-b3ee-5d9b29ce1a68	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.775573	\N
0790df8d-88b1-453b-8707-a68f17d27185	56a193c6-cb96-4d4b-b123-7d457ae4124e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.776684	\N
c466bdee-d47a-4325-b657-c7b69c76009c	108a70f8-f364-4565-bb2e-06d584866698	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.777729	\N
808a0b71-f4e3-43a1-8647-94d7ad4f84b4	947d8bae-e625-4d0a-8659-e0db8a4aa93b	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.778772	\N
63b7690e-a575-4fd0-8d26-0e5c8ed171a1	d2ea9de5-17dd-4cf0-bcad-9ccab5c1b5d9	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.779819	\N
1c36e727-ebd7-4b02-9384-5b6f9959fb80	92ba3872-821d-46b8-ad78-e26fc59c2a85	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.780884	\N
313dc5c9-ac7c-4516-9565-e1f009d7f48d	15987285-9afc-4c0f-a462-14414eb0ffd1	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.781999	\N
aadac9e1-50ca-411f-a1aa-9e396ff4a994	074ba9a8-b42c-41ee-9e6f-07b2f6dcc3ea	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.783045	\N
bf8bf2fd-b2c8-4205-8009-bd415b2254cc	667808e0-fed9-462e-8a61-a1c87415ef76	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.784071	\N
c6532e27-9ace-4f58-aa90-9d9dc243427b	d7b39622-e449-4542-9230-e3e73ea223fe	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.785111	\N
9f81ec30-013f-44e9-b3a5-b02a4afea527	314e8276-3847-4a67-83b1-96e168539108	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.78612	\N
51f77f07-1202-42a9-8b0f-c4ca2d8755e7	23201d73-9809-43c0-b9ec-f12cfc433562	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.78712	\N
a86c0e81-fc5b-4a7b-9202-8694e79c5361	2a719c1a-84d4-4509-a56a-6e80640bc6c0	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.788199	\N
2b575b4d-d60b-4f78-bdd9-2f2f170b8843	67859080-005e-446e-9f3f-893f1313cc0e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.789223	\N
e7e0ddd0-baef-4db4-ae97-8200fb85af98	700c3aae-56f1-40b0-ae5d-e8239dff6997	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.790453	\N
0751a4b4-b8fb-48e9-a736-5a55c97372aa	f30fb360-c85b-4a09-9bcd-d9abac9e50c8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.791592	\N
13a2935e-8a06-476d-99d2-55eb1ea2557c	84b0e948-1c9d-47a3-9629-0f97cced849c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.792627	\N
7678eb8b-8526-4a22-8b21-70f24fe2411b	673999a3-0205-4882-89ed-028190df4a1f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.793655	\N
a75db47d-8f00-4e10-a7ba-7a67430b9cac	bb2f1ba0-2ebe-493d-90f3-2e95af231acc	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.794708	\N
9f41886f-320f-4e7e-8ce9-d8befee88cc1	f8ce6f74-eb23-4da8-af06-472a81e1a71a	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.795751	\N
ef4ffa74-6c26-41d6-8476-ff58db260bbc	2a00942b-8b89-40b1-b824-c2431ef52f66	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.796817	\N
efc5fb78-6162-46dd-8496-6d00078a3f12	720a669a-4897-486d-9da3-4885cc5a10aa	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.797847	\N
6ede5555-cac6-4fa5-abbe-4f0f09711fe0	048bdf11-1043-4503-907a-9643ca712951	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.79885	\N
ed56a134-8631-4a69-a0e1-feeef44d10a0	6244b595-03e6-46d4-b5c9-4905320db6ba	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.799863	\N
a738f12b-f20b-461a-9911-0ffcab705c42	bd302884-4bc3-4ab2-923e-ef2ca85292db	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.800902	\N
081abbaf-ca0a-4fe3-98cd-42ed6640ef28	4036b7db-da83-4239-923c-75bedc96b8dd	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.801902	\N
54d089e6-331f-45eb-9631-9e6ccf761038	d195f2e3-0eab-49e8-8c9b-cd2585746899	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.802898	\N
f932f652-e5c4-42bf-a975-c7bdac51e7e9	c284f130-d67e-4e80-ae7c-5efe69ea2c96	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.80391	\N
2cdd00dc-5c23-4c01-b411-bdbf3812df77	b1e2d711-a913-4913-a823-e2ed7334d0da	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.804935	\N
b75702a9-4f50-4006-b07b-54b399d7d388	6ffd6bd2-673c-48de-b366-7769ee73ff56	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.80593	\N
9fda7e50-e0ee-4610-b86e-f50e9b8f4b8e	04982eb1-3893-4721-b565-24e288a11471	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.807137	\N
e1caae7b-2b5d-431c-9719-1e181f29bb15	d386b8a1-02f1-4ac1-9ead-5fc1377e1993	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.808329	\N
46be03c7-84e8-491e-81b6-2463e0af102d	4f21f7aa-c34d-4d64-a90d-86a204f91af9	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.809451	\N
19eecf0e-1ac2-4083-9325-aec038011f83	103ed435-29b0-4ca5-975f-3ebd3eca094f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.810566	\N
d46415b8-fce5-43b1-9dc9-eee8005c5e45	fb36a230-b4de-4c3b-abde-e53f08271183	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.811676	\N
aa448e7e-333f-4df0-810c-f59a618f6e05	93f914dc-dca0-4e3b-8248-62043607d234	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.812786	\N
c66e20a0-0f7d-48c7-a26d-1b5a0e13c363	631b30e0-8a06-4713-a43d-c6afbc38db22	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.813894	\N
f54cd215-2736-473c-91c0-c7d3b78607f4	c3dfbb0b-4ca0-4ff6-bf1a-c330ed19106c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.815077	\N
c9422c88-e434-402f-ac98-500700cb3dde	515a0515-d797-4703-be21-073bc8e55b3d	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.816141	\N
e475eadf-43d5-443a-8649-0d4592515d67	d942fda1-4e4b-4c03-ac7c-5fa39bed181b	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.817289	\N
e3daabce-5e69-4f49-a7bd-222eefcfba0d	bf5149e6-8747-45d2-8e86-0107fed3740f	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.818506	\N
f54bff81-057e-4a3a-9aef-dc1f8b9f5e8d	1ea12d81-7128-4a97-a464-0b7a43cae8cd	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.82028	\N
0c4242e3-f6f8-4434-a776-b5a58174e886	8cb49dc3-baf9-4fe7-9777-2c9acff0ce0a	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.821787	\N
c1eb4d15-2f26-4d7f-9116-cf35eccfd800	f2bf421c-0245-47e9-869d-807026e2480a	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.823268	\N
0df00f48-0cbf-4b0c-8b45-b1d95e6b1e6b	f557ae10-7f06-45f2-afa5-4a50dce0137e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.82553	\N
0e498909-d168-45d5-94b0-523b3918c63e	33625b79-4a50-4ce9-a6af-1d74fea662a3	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.828158	\N
b9bd6d00-dd50-489a-83c5-1bac3f682fec	52c8116b-435d-4255-9f9b-5721819cf2ae	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.830202	\N
130459a6-197f-415d-aaa6-db65baaa64f8	69a98d02-599c-4321-8271-435801439b34	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.831562	\N
c60e87a8-0b64-4760-bfe7-091722701b31	6826ce38-c99e-42bc-a52d-a5ac98638947	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.83272	\N
deb29720-f931-4a74-9c05-6ada7ba81e15	6a9f8a8a-754b-4574-aa5f-3d8403d0d1c1	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.833948	\N
410f7812-fc74-447c-9f02-90f1d4714a94	4afb6fb3-ca24-4a2b-9ee4-0aad59c652a4	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.835102	\N
1791570c-f6f9-4478-8183-814abe80cd83	3d0c09cb-ed15-41c0-b1a7-7e143115cb11	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.83636	\N
2dbb0732-5cd6-4142-b5fe-7dd349b5b2df	691fe9d1-3124-470c-94c1-e9a9ebfe35a2	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.837505	\N
031e09c1-43ab-4be2-9903-c596791cbfe4	81e6ed67-3261-483a-8a93-a61a49af87b9	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.838566	\N
b6acfc76-8fa8-43f3-a845-50101a58a460	59e4891d-1a28-4877-924e-f4eb6769d4fc	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.839669	\N
e77ab2b6-2ea9-48c7-af8e-5a9ed8a898aa	18df674d-51f8-4a46-b0a6-eaa1e75d7c40	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.841482	\N
174a26c2-5cc2-4290-9e82-6b2f315ed239	3e512524-d50a-4fbf-bcd3-d9cc223f0cf0	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.84258	\N
3055e979-e66a-4164-831b-e937814e4aad	6abe7809-bda3-4dfa-be94-ba159728f5c8	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.84365	\N
2c7bf325-efc8-4a37-91fb-edc87887e838	ce363d95-b3ca-4b71-800f-43f99fc01c83	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.844741	\N
b0c545df-12b7-40b0-8fa4-d3a7dfceb924	d3682c40-056c-4d7c-89dc-317b5c33fecf	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.845854	\N
eb4650a2-5e4e-4752-a806-324f4a1f7b44	db557db8-edc8-4c29-98b7-c66eb71e3a22	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.847073	\N
14f7dfb3-c5cf-4ef6-b52a-983820a692bd	871bd2c1-1c02-418e-bdd4-7f2edf19f9bd	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.848149	\N
d00ae66f-527e-4295-a409-ed2d8e916885	61b90ea8-b14b-4212-bcd0-82080d851df1	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.849223	\N
4c579a66-b017-4516-a9eb-d5c34bbeae45	de932f67-511c-4489-a407-4a4aa77e2d58	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.850333	\N
1da0da55-43c2-4722-9f09-c23607bdeaf2	f7171413-6505-4e8b-b6e0-145b02a8232c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.851381	\N
1d6e8932-1acd-432e-9025-aaef09964991	67f1632e-d38b-4ab1-9f9d-63f6e77e7d7c	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.852411	\N
fd1f20cc-8e01-4b5d-b5dd-040af1d4bbcc	8ae0aed9-3905-46db-9a33-ce33d86416b0	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.853435	\N
3862585b-cea5-41b5-82cc-df3c1b659a76	17e2bf5e-9f63-45ea-b68d-c5cd38a18b5e	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.854437	\N
7f99ae3e-0bc4-4536-87bb-1016a38144f8	d6015955-139f-4b4f-bd59-38c42d485142	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.85545	\N
8ae8ad62-6825-43b2-a3ed-01ef49bc49e1	c648bff0-431a-4c4b-867c-fbf27ff8fd66	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.856862	\N
3e3f1aa0-e320-4435-9e90-e8bd01f6af56	c30d46e9-0ce5-4af0-ba6f-39cde01d05a3	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.85824	\N
2f709a5a-5d9a-489c-9788-cf34783cb3b5	a947f35d-2d7b-4cf5-a504-c593f31b5b88	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.85931	\N
df95e736-4d88-44b4-8d7f-8361b9eb873b	4c682971-b238-436c-933b-da65394f69eb	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.86027	\N
cbedc586-768a-49c5-9575-696d3cf7df20	ad062ff9-f7c6-446f-ae3b-16b34f4baff5	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.861182	\N
91ffffd7-d772-4777-8fb4-eb83e0249dfa	17f52e82-2db5-4722-b3af-67d487c4dbea	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.862072	\N
972c39b9-433f-44ca-abd7-302f0fbb148b	bb7d1c51-685c-4a01-8e6f-d1ee2e085603	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.863093	\N
e45e060c-f425-46a0-8b48-81d72d469294	89d967e0-9c53-47fc-bab4-5c6b20aecce2	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.864141	\N
4e31007c-a592-4358-adcd-1e1191249614	f0134f34-1e33-446f-958c-0e06ff34c6bc	0	25	initial	Loaded from legacy roster	2025-11-05 20:28:22.865182	\N
\.


--
-- Data for Name: players; Type: TABLE DATA; Schema: public; Owner: cricket_admin
--

COPY public.players (id, club_id, team_id, name, player_type, fantasy_value, value_calculation_date, value_manually_adjusted, value_adjustment_reason, stats, performance_score, consistency_score, legacy_player_id, created_at, updated_at, created_by, multiplier, multiplier_updated_at, is_wicket_keeper) FROM stdin;
c8e66160-6491-4ba1-a68e-6d40fc8f0471	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	\N	Test Player API	\N	25	\N	f	\N	\N	\N	\N	\N	2025-11-06 08:56:58.902877	2025-11-06 08:56:58.90288	553d301a-c548-429d-8e69-087c399a3361	1.5	\N	f
01b0edbc-1255-4834-b8d6-ad3187d147c1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	DavidMasson	all-rounder	25	2025-11-05 20:28:22.631928	f	\N	{"matches": 1, "runs": 204, "batting_avg": 40.8, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 34.8, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_633	2025-11-05 20:28:22.632093	2025-11-06 09:28:58.735394	\N	1.59	2025-11-05 21:31:58.187019	f
4947b901-5b1e-440a-95d8-cfc13387e9ca	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	GurlabhSingh	batsman	25	2025-11-05 20:28:22.636578	f	\N	{"matches": 9, "runs": 251, "batting_avg": 15.69, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 36.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_038	2025-11-05 20:28:22.636725	2025-11-06 10:10:57.942438	\N	1.46	2025-11-06 10:10:57.942431	t
691fe9d1-3124-470c-94c1-e9a9ebfe35a2	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	JoostBakker	batsman	25	2025-11-05 20:28:22.835821	f	\N	{"matches": 7, "runs": 54, "batting_avg": 6.0, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_117	2025-11-05 20:28:22.83603	2025-11-06 10:11:18.057505	\N	4.49	2025-11-06 10:11:18.0575	t
0385f0dc-f7a1-40b7-aa5f-ecb3078408e7	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	SumeetDiwan	all-rounder	25	2025-11-05 20:28:22.442927	f	\N	{"matches": 2, "runs": 324, "batting_avg": 36.0, "strike_rate": 0.0, "wickets": 15, "bowling_avg": 18.27, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_153	2025-11-05 20:28:22.443136	2025-11-06 09:28:58.735397	\N	0.95	2025-11-05 21:31:58.187054	f
03b07307-b139-4b3f-8b53-f8eacfc98369	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	NaveenRajasekaran	bowler	25	2025-11-05 20:28:22.740052	f	\N	{"matches": 1, "runs": 13, "batting_avg": 6.5, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 32.71, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_578	2025-11-05 20:28:22.740278	2025-11-06 09:28:58.735397	\N	3.56	2025-11-05 21:31:58.187056	f
04761f4e-d407-42e4-931b-a3933ec753f0	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	SachinPeiris	batsman	25	2025-11-05 20:28:22.546492	f	\N	{"matches": 1, "runs": 401, "batting_avg": 21.11, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_345	2025-11-05 20:28:22.546638	2025-11-06 09:28:58.735398	\N	0.98	2025-11-05 21:31:58.187059	f
048bdf11-1043-4503-907a-9643ca712951	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	KshitijkumarPadhy	batsman	25	2025-11-05 20:28:22.797414	f	\N	{"matches": 1, "runs": 87, "batting_avg": 10.88, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_663	2025-11-05 20:28:22.797571	2025-11-06 09:28:58.735398	\N	4.11	2025-11-05 21:31:58.187061	f
04982eb1-3893-4721-b565-24e288a11471	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	ShauryaThakur	batsman	25	2025-11-05 20:28:22.805507	f	\N	{"matches": 1, "runs": 80, "batting_avg": 8.0, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_330	2025-11-05 20:28:22.805661	2025-11-06 09:28:58.735398	\N	4.19	2025-11-05 21:31:58.187065	f
063a8f6a-dda8-48b4-a1c4-af72700dbcf5	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	ImranQuderty	all-rounder	25	2025-11-05 20:28:22.333178	f	\N	{"matches": 3, "runs": 497, "batting_avg": 29.24, "strike_rate": 0.0, "wickets": 37, "bowling_avg": 18.32, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_099	2025-11-05 20:28:22.33337	2025-11-06 09:28:58.735406	\N	0.85	2025-11-05 21:31:58.187068	f
0661de40-7387-4ffe-b371-3bd8cfa34d96	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	SubhanAshfaq	all-rounder	25	2025-11-05 20:28:22.516373	f	\N	{"matches": 2, "runs": 258, "batting_avg": 19.85, "strike_rate": 0.0, "wickets": 11, "bowling_avg": 33.64, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_466	2025-11-05 20:28:22.516521	2025-11-06 09:28:58.735407	\N	0.98	2025-11-05 21:31:58.18707	f
06c7b178-37ec-4728-8f18-9bed72282970	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	AgampreetSingh	all-rounder	25	2025-11-05 20:28:22.747141	f	\N	{"matches": 1, "runs": 30, "batting_avg": 4.29, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 33.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_590	2025-11-05 20:28:22.747288	2025-11-06 09:28:58.735407	\N	3.63	2025-11-05 21:31:58.187073	f
06e08974-ea2f-4e58-99a9-e25f97f208f8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	RavindraDayaram	bowler	25	2025-11-05 20:28:22.65247	f	\N	{"matches": 2, "runs": 47, "batting_avg": 3.62, "strike_rate": 0.0, "wickets": 10, "bowling_avg": 63.1, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_476	2025-11-05 20:28:22.652611	2025-11-06 09:28:58.735407	\N	2.55	2025-11-05 21:31:58.187075	f
0737595b-79c6-4540-be98-cd97c6c536a9	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	SauravNarain	bowler	25	2025-11-05 20:28:22.657633	f	\N	{"matches": 2, "runs": 41, "batting_avg": 3.73, "strike_rate": 0.0, "wickets": 10, "bowling_avg": 41.1, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_482	2025-11-05 20:28:22.657792	2025-11-06 09:28:58.735407	\N	2.6	2025-11-05 21:31:58.187077	f
074ba9a8-b42c-41ee-9e6f-07b2f6dcc3ea	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	KrishaanMali	bowler	25	2025-11-05 20:28:22.781538	f	\N	{"matches": 1, "runs": 28, "batting_avg": 9.33, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 31.25, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_507	2025-11-05 20:28:22.781707	2025-11-06 09:28:58.735408	\N	4.11	2025-11-05 21:31:58.187078	f
077e2e70-b575-4a70-83b0-0c3ab3c695e2	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	SujervanNageswaran	all-rounder	25	2025-11-05 20:28:22.692077	f	\N	{"matches": 1, "runs": 50, "batting_avg": 6.25, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 26.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_275	2025-11-05 20:28:22.692246	2025-11-06 09:28:58.735408	\N	2.98	2025-11-05 21:31:58.187081	f
083ee276-cd5d-4d52-9452-df46f531b8e8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	MandeepSingh	all-rounder	25	2025-11-05 20:28:22.319081	f	\N	{"matches": 2, "runs": 1082, "batting_avg": 54.1, "strike_rate": 0.0, "wickets": 32, "bowling_avg": 26.19, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_366	2025-11-05 20:28:22.319397	2025-11-06 09:28:58.735408	\N	0.75	2025-11-05 21:31:58.187084	f
08e56cfd-3a76-4814-8911-2e08e1e3f60c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	ZahidIslam	all-rounder	25	2025-11-05 20:28:22.608336	f	\N	{"matches": 1, "runs": 130, "batting_avg": 18.57, "strike_rate": 0.0, "wickets": 10, "bowling_avg": 27.3, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_432	2025-11-05 20:28:22.608493	2025-11-06 09:28:58.735408	\N	1.51	2025-11-05 21:31:58.187087	f
09883877-87ce-4135-a3fc-86ce3a18ba89	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	VivekTiwari	batsman	25	2025-11-05 20:28:22.630675	f	\N	{"matches": 7, "runs": 121, "batting_avg": 15.13, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 39.11, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_086	2025-11-05 20:28:22.630821	2025-11-06 09:28:58.735408	\N	1.87	2025-11-05 21:31:58.187091	f
0b0b3062-599f-4029-a129-ea0428a838ef	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	AvnishChaudhary	batsman	25	2025-11-05 20:28:22.643962	f	\N	{"matches": 6, "runs": 254, "batting_avg": 25.4, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 63.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_173	2025-11-05 20:28:22.64414	2025-11-06 09:28:58.735409	\N	1.58	2025-11-05 21:31:58.187092	f
0b3f5846-77a6-4c66-bfdb-59a38242659e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	HoneyWilliam	all-rounder	25	2025-11-05 20:28:22.646963	f	\N	{"matches": 2, "runs": 101, "batting_avg": 9.18, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 29.22, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_285	2025-11-05 20:28:22.647121	2025-11-06 09:28:58.735409	\N	2.16	2025-11-05 21:31:58.187094	f
0b55cf2f-3083-4f7d-b54a-a4955390ffe1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	JunedIqbal	batsman	25	2025-11-05 20:28:22.582969	f	\N	{"matches": 1, "runs": 357, "batting_avg": 27.46, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_649	2025-11-05 20:28:22.583116	2025-11-06 09:28:58.735409	\N	0.99	2025-11-05 21:31:58.187096	f
0b8537eb-86ba-490f-a11a-4962d0e794f8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	AbhilashPanicker	all-rounder	25	2025-11-05 20:28:22.407478	f	\N	{"matches": 2, "runs": 203, "batting_avg": 29.0, "strike_rate": 0.0, "wickets": 26, "bowling_avg": 11.31, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_524	2025-11-05 20:28:22.407624	2025-11-06 09:28:58.735409	\N	0.94	2025-11-05 21:31:58.187098	f
0c2802ba-dad1-480f-b834-adc04b2f3ac3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	GauravNivsarkar	all-rounder	25	2025-11-05 20:28:22.518608	f	\N	{"matches": 1, "runs": 106, "batting_avg": 17.67, "strike_rate": 0.0, "wickets": 18, "bowling_avg": 13.17, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_159	2025-11-05 20:28:22.518749	2025-11-06 09:28:58.735409	\N	0.99	2025-11-05 21:31:58.187101	f
0c8c23b4-a9b5-467c-93b2-1f8813eadf47	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	DarshAbhinay	all-rounder	25	2025-11-05 20:28:22.441821	f	\N	{"matches": 2, "runs": 239, "batting_avg": 21.73, "strike_rate": 0.0, "wickets": 19, "bowling_avg": 22.89, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_375	2025-11-05 20:28:22.442007	2025-11-06 09:28:58.73541	\N	0.96	2025-11-05 21:31:58.187103	f
0c98bd73-1bed-4a9d-b0f9-948e8df45c81	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	KeaganBromilow	batsman	25	2025-11-05 20:28:22.766518	f	\N	{"matches": 1, "runs": 120, "batting_avg": 40.0, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_073	2025-11-05 20:28:22.766661	2025-11-06 09:28:58.73541	\N	3.67	2025-11-05 21:31:58.187105	f
0cf396df-4bc6-462c-af0f-b3e519b9c354	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	KulteghSingh	all-rounder	25	2025-11-05 20:28:22.638136	f	\N	{"matches": 1, "runs": 155, "batting_avg": 14.09, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 43.86, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_641	2025-11-05 20:28:22.638283	2025-11-06 09:28:58.73541	\N	1.84	2025-11-05 21:31:58.187107	f
0dd09299-c0e4-4576-923f-6b554acb25bc	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	AdilAnsari	all-rounder	25	2025-11-05 20:28:22.722459	f	\N	{"matches": 2, "runs": 67, "batting_avg": 13.4, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 31.67, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_258	2025-11-05 20:28:22.722601	2025-11-06 09:28:58.73541	\N	3.25	2025-11-05 21:31:58.18711	f
0f5d36e8-35e5-406c-a922-e4404fdb0bf8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	BhargavNallapu	all-rounder	25	2025-11-05 20:28:22.74428	f	\N	{"matches": 1, "runs": 40, "batting_avg": 13.33, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 32.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_190	2025-11-05 20:28:22.744431	2025-11-06 09:28:58.735411	\N	3.54	2025-11-05 21:31:58.187116	f
103ed435-29b0-4ca5-975f-3ebd3eca094f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	AyaanAbhilash	batsman	25	2025-11-05 20:28:22.808996	f	\N	{"matches": 1, "runs": 39, "batting_avg": 13.0, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 74.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_541	2025-11-05 20:28:22.80917	2025-11-06 09:28:58.735411	\N	4.33	2025-11-05 21:31:58.187125	f
108a70f8-f364-4565-bb2e-06d584866698	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	AjayKumar	bowler	25	2025-11-05 20:28:22.776226	f	\N	{"matches": 4, "runs": 2, "batting_avg": 0.0, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 51.2, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_041	2025-11-05 20:28:22.776392	2025-11-06 09:28:58.735411	\N	4.12	2025-11-05 21:31:58.187131	f
111d39ff-a245-4caf-b466-0dbfd7a31924	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	SharifollahSherzad	bowler	25	2025-11-05 20:28:22.602929	f	\N	{"matches": 1, "runs": 11, "batting_avg": 1.83, "strike_rate": 0.0, "wickets": 15, "bowling_avg": 25.47, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_050	2025-11-05 20:28:22.603074	2025-11-06 09:28:58.735411	\N	1.73	2025-11-05 21:31:58.187133	f
11aa9544-ea4e-468a-ae52-5b4397f2a852	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	ManzoorTarake	all-rounder	25	2025-11-05 20:28:22.389603	f	\N	{"matches": 1, "runs": 209, "batting_avg": 13.93, "strike_rate": 0.0, "wickets": 30, "bowling_avg": 19.07, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_133	2025-11-05 20:28:22.389763	2025-11-06 09:28:58.735412	\N	0.93	2025-11-05 21:31:58.187136	f
12853a6b-b381-4424-8295-54daf3905cd1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	AdnanAhmad	all-rounder	25	2025-11-05 20:28:22.342032	f	\N	{"matches": 2, "runs": 656, "batting_avg": 28.52, "strike_rate": 0.0, "wickets": 24, "bowling_avg": 25.13, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_568	2025-11-05 20:28:22.34227	2025-11-06 09:28:58.735412	\N	0.86	2025-11-05 21:31:58.187138	f
12c69d23-9759-4a41-9195-f15bb384083e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	HimanshuTonk	all-rounder	25	2025-11-05 20:28:22.427076	f	\N	{"matches": 2, "runs": 277, "batting_avg": 27.7, "strike_rate": 0.0, "wickets": 19, "bowling_avg": 21.68, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_247	2025-11-05 20:28:22.427253	2025-11-06 09:28:58.735412	\N	0.95	2025-11-05 21:31:58.187139	f
132d0dce-6d56-4a5c-8fa9-58f7ea63f16c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	AaravManohar	all-rounder	25	2025-11-05 20:28:22.444238	f	\N	{"matches": 1, "runs": 238, "batting_avg": 19.83, "strike_rate": 0.0, "wickets": 19, "bowling_avg": 22.84, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_639	2025-11-05 20:28:22.444429	2025-11-06 09:28:58.735412	\N	0.96	2025-11-05 21:31:58.187143	f
134b2220-525e-47d8-abb6-58cd86018c97	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	ShaikhBadiujzama	all-rounder	25	2025-11-05 20:28:22.330644	f	\N	{"matches": 2, "runs": 99, "batting_avg": 8.25, "strike_rate": 0.0, "wickets": 62, "bowling_avg": 10.53, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_007	2025-11-05 20:28:22.330833	2025-11-06 09:28:58.735412	\N	0.85	2025-11-05 21:31:58.187145	f
136a5d4a-4904-4756-8ab1-0fcc738ecf38	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	SaimMian	all-rounder	25	2025-11-05 20:28:22.633777	f	\N	{"matches": 1, "runs": 42, "batting_avg": 6.0, "strike_rate": 0.0, "wickets": 12, "bowling_avg": 29.58, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_644	2025-11-05 20:28:22.633945	2025-11-06 09:28:58.735413	\N	2.13	2025-11-05 21:31:58.187147	f
13d7b625-f44c-4dbd-9edc-e03caeb11e90	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	ZinedineKhawaja	bowler	25	2025-11-05 20:28:22.753623	f	\N	{"matches": 2, "runs": 48, "batting_avg": 6.86, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 29.2, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_614	2025-11-05 20:28:22.753771	2025-11-06 09:28:58.735413	\N	3.69	2025-11-05 21:31:58.187148	f
1564dcfe-6b5a-4522-b699-ff6c39dfd2e5	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	ShubhamChhikara	all-rounder	25	2025-11-05 20:28:22.3604	f	\N	{"matches": 1, "runs": 799, "batting_avg": 57.07, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 32.11, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_537	2025-11-05 20:28:22.360556	2025-11-06 09:28:58.735413	\N	0.88	2025-11-05 21:31:58.187153	f
15987285-9afc-4c0f-a462-14414eb0ffd1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	AdityaNavandar	batsman	25	2025-11-05 20:28:22.780444	f	\N	{"matches": 1, "runs": 105, "batting_avg": 10.5, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_582	2025-11-05 20:28:22.780606	2025-11-06 09:28:58.735413	\N	3.89	2025-11-05 21:31:58.187154	f
15e000ff-0164-4a3d-adbb-247e94b9512f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	VasanthSekar	batsman	25	2025-11-05 20:28:22.457207	f	\N	{"matches": 2, "runs": 531, "batting_avg": 24.14, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 26.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_263	2025-11-05 20:28:22.457351	2025-11-06 09:28:58.735413	\N	0.95	2025-11-05 21:31:58.187156	f
16dc2133-c16c-415d-bfc6-b629e957e9fe	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	NaveenSingh	all-rounder	25	2025-11-05 20:28:22.379683	f	\N	{"matches": 1, "runs": 279, "batting_avg": 23.25, "strike_rate": 0.0, "wickets": 29, "bowling_avg": 10.93, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_683	2025-11-05 20:28:22.379836	2025-11-06 09:28:58.735414	\N	0.92	2025-11-05 21:31:58.187162	f
1757a48d-48cc-4981-b5a1-be2e36ea1f4a	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	MohitKumar	all-rounder	25	2025-11-05 20:28:22.505249	f	\N	{"matches": 2, "runs": 237, "batting_avg": 21.55, "strike_rate": 0.0, "wickets": 13, "bowling_avg": 50.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_014	2025-11-05 20:28:22.505392	2025-11-06 09:28:58.735414	\N	0.98	2025-11-05 21:31:58.187165	f
177ce35d-4c34-4c79-b6a7-265e69604405	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	IrfanAlim	batsman	25	2025-11-05 20:28:22.591147	f	\N	{"matches": 7, "runs": 340, "batting_avg": 34.0, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_082	2025-11-05 20:28:22.591292	2025-11-06 09:28:58.735414	\N	0.99	2025-11-05 21:31:58.187169	f
17e2bf5e-9f63-45ea-b68d-c5cd38a18b5e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	RoonavNarayanan	bowler	25	2025-11-05 20:28:22.853012	f	\N	{"matches": 1, "runs": 0, "batting_avg": 0.0, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 48.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_297	2025-11-05 20:28:22.85317	2025-11-06 09:28:58.735415	\N	4.85	2025-11-05 21:31:58.187171	f
17f52e82-2db5-4722-b3af-67d487c4dbea	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	ZahabiaGhadiali	batsman	25	2025-11-05 20:28:22.860779	f	\N	{"matches": 1, "runs": 3, "batting_avg": 1.5, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_363	2025-11-05 20:28:22.860954	2025-11-06 09:28:58.735415	\N	4.98	2025-11-05 21:31:58.187173	f
180b9284-2aa9-4b36-a9a1-e82dc089ca73	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	AnoopChoudhary	all-rounder	25	2025-11-05 20:28:22.471306	f	\N	{"matches": 1, "runs": 357, "batting_avg": 29.75, "strike_rate": 0.0, "wickets": 10, "bowling_avg": 22.9, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_479	2025-11-05 20:28:22.471456	2025-11-06 09:28:58.735415	\N	0.96	2025-11-05 21:31:58.187174	f
18df674d-51f8-4a46-b0a6-eaa1e75d7c40	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	GijsEvers	batsman	25	2025-11-05 20:28:22.839196	f	\N	{"matches": 2, "runs": 43, "batting_avg": 14.33, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_136	2025-11-05 20:28:22.839364	2025-11-06 09:28:58.735416	\N	4.61	2025-11-05 21:31:58.187176	f
192315d2-23b8-4668-b978-039183ac0036	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	SiddarthMadhavan	batsman	25	2025-11-05 20:28:22.772509	f	\N	{"matches": 3, "runs": 42, "batting_avg": 10.5, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 21.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_253	2025-11-05 20:28:22.772665	2025-11-06 09:28:58.735416	\N	3.98	2025-11-05 21:31:58.187178	f
197fa640-0c72-4d2f-a172-20de8af78b25	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	IzhaanSayed	all-rounder	25	2025-11-05 20:28:22.324974	f	\N	{"matches": 13, "runs": 411, "batting_avg": 22.83, "strike_rate": 0.0, "wickets": 50, "bowling_avg": 14.04, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_141	2025-11-05 20:28:22.325262	2025-11-06 09:28:58.735416	\N	0.83	2025-11-05 21:31:58.187183	f
1a8cfdb4-dce6-425e-bd94-3b37e7edfb8c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	RachitGupta	all-rounder	25	2025-11-05 20:28:22.720386	f	\N	{"matches": 1, "runs": 131, "batting_avg": 16.38, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 59.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_279	2025-11-05 20:28:22.720521	2025-11-06 09:28:58.735416	\N	3.04	2025-11-05 21:31:58.187187	f
1ab0dd7e-3d26-4f84-908a-90180b249f0b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	SabinSumghershanan	batsman	25	2025-11-05 20:28:22.704221	f	\N	{"matches": 1, "runs": 160, "batting_avg": 22.86, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 47.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_678	2025-11-05 20:28:22.704372	2025-11-06 09:28:58.735416	\N	2.78	2025-11-05 21:31:58.187189	f
1b6f3ee8-3777-4a5f-a2eb-8fe91af4b15f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	ThomasPasierowski	all-rounder	25	2025-11-05 20:28:22.383336	f	\N	{"matches": 1, "runs": 405, "batting_avg": 31.15, "strike_rate": 0.0, "wickets": 22, "bowling_avg": 21.91, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_238	2025-11-05 20:28:22.383487	2025-11-06 09:28:58.735417	\N	0.92	2025-11-05 21:31:58.187191	f
1bbf21b6-da24-4b08-9b2d-81b635f51fb4	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	GaganGaba	batsman	25	2025-11-05 20:28:22.467728	f	\N	{"matches": 5, "runs": 553, "batting_avg": 36.87, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 30.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_100	2025-11-05 20:28:22.467867	2025-11-06 09:28:58.735417	\N	0.95	2025-11-05 21:31:58.187193	f
1c2caa0b-f9a7-4950-a4a8-60288994fc3d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	DevanshuArya	bowler	25	2025-11-05 20:28:22.435772	f	\N	{"matches": 10, "runs": 46, "batting_avg": 9.2, "strike_rate": 0.0, "wickets": 28, "bowling_avg": 17.96, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_155	2025-11-05 20:28:22.435936	2025-11-06 09:28:58.735417	\N	0.96	2025-11-05 21:31:58.187194	f
1c625beb-5b44-407a-b04b-a405a372bbfb	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	FidaAli	bowler	25	2025-11-05 20:28:22.667254	f	\N	{"matches": 3, "runs": 71, "batting_avg": 4.73, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 42.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_036	2025-11-05 20:28:22.667399	2025-11-06 09:28:58.735417	\N	2.74	2025-11-05 21:31:58.187196	f
1c71fe37-c931-4bcb-88d1-8679e22b01ba	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	BhathiyaGunathilaka	all-rounder	25	2025-11-05 20:28:22.414031	f	\N	{"matches": 1, "runs": 258, "batting_avg": 18.43, "strike_rate": 0.0, "wickets": 22, "bowling_avg": 24.59, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_276	2025-11-05 20:28:22.414187	2025-11-06 09:28:58.735418	\N	0.94	2025-11-05 21:31:58.187201	f
1cbf5983-b806-4bc9-b8ff-04226fa78478	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	SrijanSingh	all-rounder	25	2025-11-05 20:28:22.385133	f	\N	{"matches": 1, "runs": 317, "batting_avg": 18.65, "strike_rate": 0.0, "wickets": 26, "bowling_avg": 22.73, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_470	2025-11-05 20:28:22.38528	2025-11-06 09:28:58.735418	\N	0.92	2025-11-05 21:31:58.187208	f
1e6b8c8c-d6ca-4095-996c-1d7c959b53d3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	WaleedEjaz	all-rounder	25	2025-11-05 20:28:22.375241	f	\N	{"matches": 2, "runs": 733, "batting_avg": 45.81, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 20.78, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_378	2025-11-05 20:28:22.375467	2025-11-06 09:28:58.735418	\N	0.89	2025-11-05 21:31:58.187215	f
1ea12d81-7128-4a97-a464-0b7a43cae8cd	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	UlcoUmans	batsman	25	2025-11-05 20:28:22.817997	f	\N	{"matches": 3, "runs": 44, "batting_avg": 11.0, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 14.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_637	2025-11-05 20:28:22.818174	2025-11-06 09:28:58.735418	\N	4.44	2025-11-05 21:31:58.187218	f
1eebe7f5-e124-4b9e-affd-553fe02a510d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	AmiteshKamani	batsman	25	2025-11-05 20:28:22.64776	f	\N	{"matches": 7, "runs": 163, "batting_avg": 12.54, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 26.33, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_069	2025-11-05 20:28:22.647922	2025-11-06 09:28:58.735418	\N	1.95	2025-11-05 21:31:58.187221	f
1f2e7f75-c1a3-43d7-b6fd-153350e4265b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	DaniyalKhan	all-rounder	25	2025-11-05 20:28:22.60563	f	\N	{"matches": 2, "runs": 154, "batting_avg": 30.8, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 33.22, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_438	2025-11-05 20:28:22.605773	2025-11-06 09:28:58.735419	\N	1.39	2025-11-05 21:31:58.187222	f
1f8ecb5d-fbd0-4a9b-bfa7-394fc0363096	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	JaganNarayanamoorthy	batsman	25	2025-11-05 20:28:22.660994	f	\N	{"matches": 1, "runs": 231, "batting_avg": 23.1, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_323	2025-11-05 20:28:22.661144	2025-11-06 09:28:58.735419	\N	2.07	2025-11-05 21:31:58.187224	f
1fa421bc-f876-466c-9e39-966932c45c94	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	GouravSharma	bowler	25	2025-11-05 20:28:22.418276	f	\N	{"matches": 1, "runs": 23, "batting_avg": 3.29, "strike_rate": 0.0, "wickets": 32, "bowling_avg": 20.59, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_244	2025-11-05 20:28:22.418426	2025-11-06 09:28:58.735419	\N	0.96	2025-11-05 21:31:58.187225	f
1fe65eae-61b5-4649-98b7-31f27bfe7588	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	AshwinOppu	batsman	25	2025-11-05 20:28:22.578367	f	\N	{"matches": 1, "runs": 363, "batting_avg": 27.92, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_431	2025-11-05 20:28:22.578517	2025-11-06 09:28:58.735419	\N	0.99	2025-11-05 21:31:58.187227	f
1ff50c17-6c45-42fd-9e01-01f970a43a46	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	SatvinderSingh	all-rounder	25	2025-11-05 20:28:22.613297	f	\N	{"matches": 1, "runs": 148, "batting_avg": 9.25, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 29.33, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_725	2025-11-05 20:28:22.613438	2025-11-06 09:28:58.735419	\N	1.48	2025-11-05 21:31:58.187229	f
207953c2-526a-4755-8701-b6fe45556579	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	ShujatAli	all-rounder	25	2025-11-05 20:28:22.350355	f	\N	{"matches": 1, "runs": 582, "batting_avg": 36.38, "strike_rate": 0.0, "wickets": 22, "bowling_avg": 24.27, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_032	2025-11-05 20:28:22.350506	2025-11-06 09:28:58.735419	\N	0.88	2025-11-05 21:31:58.187232	f
20822aac-2350-4142-88a5-e18a5cfa1612	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	AbhaySingh	all-rounder	25	2025-11-05 20:28:22.754578	f	\N	{"matches": 1, "runs": 73, "batting_avg": 12.17, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 43.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_709	2025-11-05 20:28:22.754724	2025-11-06 09:28:58.73542	\N	3.64	2025-11-05 21:31:58.187233	f
208f6a72-aa6a-431f-a045-4a46f9462b23	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	VijayTomar	bowler	25	2025-11-05 20:28:22.388693	f	\N	{"matches": 11, "runs": 167, "batting_avg": 18.56, "strike_rate": 0.0, "wickets": 32, "bowling_avg": 20.19, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_166	2025-11-05 20:28:22.388839	2025-11-06 09:28:58.73542	\N	0.93	2025-11-05 21:31:58.187235	f
2094b356-2b83-4d4a-84ff-b92ce9c0074e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	DebrupDasgupta	batsman	25	2025-11-05 20:28:22.696174	f	\N	{"matches": 1, "runs": 198, "batting_avg": 14.14, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_365	2025-11-05 20:28:22.696322	2025-11-06 09:28:58.73542	\N	2.55	2025-11-05 21:31:58.187237	f
20c3ebc6-b60d-4bd1-99bb-c912ed5b5db1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	UmerMir	all-rounder	25	2025-11-05 20:28:22.372911	f	\N	{"matches": 2, "runs": 800, "batting_avg": 28.57, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 27.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_130	2025-11-05 20:28:22.373068	2025-11-06 09:28:58.73542	\N	0.89	2025-11-05 21:31:58.187247	f
20f79e8f-08ee-4e0f-addb-c50863ff627e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	TacoKuijers	all-rounder	25	2025-11-05 20:28:22.729427	f	\N	{"matches": 1, "runs": 78, "batting_avg": 15.6, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 47.6, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_361	2025-11-05 20:28:22.72957	2025-11-06 09:28:58.73542	\N	3.35	2025-11-05 21:31:58.187249	f
22cd8921-9675-4dab-9711-12b4e2529088	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	HarshRathore	all-rounder	25	2025-11-05 20:28:22.343335	f	\N	{"matches": 1, "runs": 634, "batting_avg": 21.13, "strike_rate": 0.0, "wickets": 25, "bowling_avg": 20.08, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_083	2025-11-05 20:28:22.343523	2025-11-06 09:28:58.735421	\N	0.86	2025-11-05 21:31:58.187254	f
23201d73-9809-43c0-b9ec-f12cfc433562	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	EdwardThomas	bowler	25	2025-11-05 20:28:22.7857	f	\N	{"matches": 4, "runs": 21, "batting_avg": 5.25, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 27.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_121	2025-11-05 20:28:22.78586	2025-11-06 09:28:58.735421	\N	4.18	2025-11-05 21:31:58.187258	f
239fb51b-611d-4bae-9bab-5d05f2ae0b62	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	VivekSingh	all-rounder	25	2025-11-05 20:28:22.494397	f	\N	{"matches": 1, "runs": 31, "batting_avg": 15.5, "strike_rate": 0.0, "wickets": 23, "bowling_avg": 17.43, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_731	2025-11-05 20:28:22.494546	2025-11-06 09:28:58.735421	\N	0.98	2025-11-05 21:31:58.187259	f
249e11e6-df0a-4bab-8697-88494377480e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	VigneshAsokan	batsman	25	2025-11-05 20:28:22.771492	f	\N	{"matches": 1, "runs": 79, "batting_avg": 11.29, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 110.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_113	2025-11-05 20:28:22.771648	2025-11-06 09:28:58.735421	\N	3.89	2025-11-05 21:31:58.187261	f
2559e411-7604-42fb-b602-132767ed8f92	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	AyaanshSehgal	batsman	25	2025-11-05 20:28:22.36409	f	\N	{"matches": 16, "runs": 476, "batting_avg": 22.67, "strike_rate": 0.0, "wickets": 23, "bowling_avg": 21.35, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_022	2025-11-05 20:28:22.364264	2025-11-06 09:28:58.735422	\N	0.9	2025-11-05 21:31:58.187266	f
259e50e6-c758-4861-860f-7b667cb84078	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	AbhishekSharma	all-rounder	25	2025-11-05 20:28:22.523052	f	\N	{"matches": 1, "runs": 94, "batting_avg": 13.43, "strike_rate": 0.0, "wickets": 18, "bowling_avg": 10.94, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_690	2025-11-05 20:28:22.523222	2025-11-06 09:28:58.735422	\N	0.99	2025-11-05 21:31:58.187268	f
261350c4-3152-4306-b717-7d42cf5b7c28	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	DaniyalAdnan	batsman	25	2025-11-05 20:28:22.529547	f	\N	{"matches": 15, "runs": 160, "batting_avg": 9.41, "strike_rate": 0.0, "wickets": 14, "bowling_avg": 28.79, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_034	2025-11-05 20:28:22.529694	2025-11-06 09:28:58.735422	\N	0.99	2025-11-05 21:31:58.18727	f
2641ff16-de10-4600-b491-8f6d23f36a66	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	RutgerDomhoff	all-rounder	25	2025-11-05 20:28:22.66455	f	\N	{"matches": 1, "runs": 102, "batting_avg": 12.75, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 17.86, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_597	2025-11-05 20:28:22.664709	2025-11-06 09:28:58.735422	\N	2.6	2025-11-05 21:31:58.187271	f
265f355b-b504-4857-afc5-893ec78e6936	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	UvarajThangavel	all-rounder	25	2025-11-05 20:28:22.482353	f	\N	{"matches": 1, "runs": 56, "batting_avg": 18.67, "strike_rate": 0.0, "wickets": 23, "bowling_avg": 14.17, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_538	2025-11-05 20:28:22.482562	2025-11-06 09:28:58.735423	\N	0.98	2025-11-05 21:31:58.187273	f
26cc3e4a-f04e-4879-9e5c-1c2464611932	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	ShirazAhmad	all-rounder	25	2025-11-05 20:28:22.357188	f	\N	{"matches": 1, "runs": 306, "batting_avg": 23.54, "strike_rate": 0.0, "wickets": 33, "bowling_avg": 15.64, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_640	2025-11-05 20:28:22.357341	2025-11-06 09:28:58.735423	\N	0.9	2025-11-05 21:31:58.187274	f
27fa5307-412a-46fa-b380-5f01004f58e7	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	RahulKumar	all-rounder	25	2025-11-05 20:28:22.411127	f	\N	{"matches": 2, "runs": 101, "batting_avg": 16.83, "strike_rate": 0.0, "wickets": 30, "bowling_avg": 17.7, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_124	2025-11-05 20:28:22.411285	2025-11-06 09:28:58.735423	\N	0.95	2025-11-05 21:31:58.187276	f
290e0a56-4f5b-48c5-a696-71d3d36b54af	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	HashimMahmood	all-rounder	25	2025-11-05 20:28:22.510682	f	\N	{"matches": 2, "runs": 201, "batting_avg": 25.13, "strike_rate": 0.0, "wickets": 14, "bowling_avg": 25.86, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_390	2025-11-05 20:28:22.510828	2025-11-06 09:28:58.735423	\N	0.98	2025-11-05 21:31:58.187283	f
299c3464-0350-4493-89b4-ad8fd31112fb	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	NaeemNasir	batsman	25	2025-11-05 20:28:22.38777	f	\N	{"matches": 9, "runs": 394, "batting_avg": 30.31, "strike_rate": 0.0, "wickets": 22, "bowling_avg": 11.91, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_024	2025-11-05 20:28:22.38793	2025-11-06 09:28:58.735423	\N	0.92	2025-11-05 21:31:58.187287	f
2a00942b-8b89-40b1-b824-c2431ef52f66	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	TivonAnanda	batsman	25	2025-11-05 20:28:22.795319	f	\N	{"matches": 1, "runs": 54, "batting_avg": 6.75, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 55.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_607	2025-11-05 20:28:22.795484	2025-11-06 09:28:58.735424	\N	4.18	2025-11-05 21:31:58.18729	f
2a0b386d-0d09-41c2-b73f-eb8cb8ec95e4	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	KeshavNarula	all-rounder	25	2025-11-05 20:28:22.447161	f	\N	{"matches": 2, "runs": 212, "batting_avg": 53.0, "strike_rate": 0.0, "wickets": 20, "bowling_avg": 34.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_104	2025-11-05 20:28:22.447312	2025-11-06 09:28:58.735424	\N	0.96	2025-11-05 21:31:58.187292	f
2a719c1a-84d4-4509-a56a-6e80640bc6c0	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	MuhilanNatarajan	batsman	25	2025-11-05 20:28:22.786693	f	\N	{"matches": 1, "runs": 79, "batting_avg": 26.33, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 31.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_450	2025-11-05 20:28:22.78685	2025-11-06 09:28:58.735424	\N	4.05	2025-11-05 21:31:58.187293	f
2b07ffa7-fdec-42da-8995-ff57965dbd84	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	JayasimhaRao	all-rounder	25	2025-11-05 20:28:22.43401	f	\N	{"matches": 2, "runs": 273, "batting_avg": 24.82, "strike_rate": 0.0, "wickets": 18, "bowling_avg": 22.39, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_101	2025-11-05 20:28:22.434155	2025-11-06 09:28:58.735424	\N	0.95	2025-11-05 21:31:58.187297	f
2b178f36-ddee-44e5-b415-798eff08671d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	KarthickSasikumar	all-rounder	25	2025-11-05 20:28:22.594772	f	\N	{"matches": 1, "runs": 106, "batting_avg": 21.2, "strike_rate": 0.0, "wickets": 12, "bowling_avg": 19.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_566	2025-11-05 20:28:22.594929	2025-11-06 09:28:58.735424	\N	1.39	2025-11-05 21:31:58.187299	f
2bccfd8a-fc68-4093-8493-cfb83321b895	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	JeroenAlderliesten	bowler	25	2025-11-05 20:28:22.531384	f	\N	{"matches": 2, "runs": 32, "batting_avg": 8.0, "strike_rate": 0.0, "wickets": 19, "bowling_avg": 23.95, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_381	2025-11-05 20:28:22.531554	2025-11-06 09:28:58.735425	\N	0.99	2025-11-05 21:31:58.187301	f
2c58831b-0786-4c4a-8c06-fae96d9bee40	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	HashimMalik	all-rounder	25	2025-11-05 20:28:22.669163	f	\N	{"matches": 1, "runs": 40, "batting_avg": 10.0, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 21.89, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_483	2025-11-05 20:28:22.669307	2025-11-06 09:28:58.735425	\N	2.84	2025-11-05 21:31:58.187303	f
2c967cc2-d539-4e9f-9e61-bdb26721f368	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	MehrabMarri	all-rounder	25	2025-11-05 20:28:22.629726	f	\N	{"matches": 2, "runs": 165, "batting_avg": 16.5, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 24.86, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_292	2025-11-05 20:28:22.629862	2025-11-06 09:28:58.735425	\N	1.69	2025-11-05 21:31:58.187304	f
2ce403ab-50af-4529-9a66-78d21f64fde7	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	VivekKumar	all-rounder	25	2025-11-05 20:28:22.347488	f	\N	{"matches": 1, "runs": 573, "batting_avg": 30.16, "strike_rate": 0.0, "wickets": 24, "bowling_avg": 14.67, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_446	2025-11-05 20:28:22.347654	2025-11-06 09:28:58.735425	\N	0.88	2025-11-05 21:31:58.187306	f
2d0b5169-8ef7-49be-bf2d-fe63a5049634	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	AjitYadav	all-rounder	25	2025-11-05 20:28:22.420177	f	\N	{"matches": 2, "runs": 203, "batting_avg": 20.3, "strike_rate": 0.0, "wickets": 24, "bowling_avg": 21.33, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_161	2025-11-05 20:28:22.420331	2025-11-06 09:28:58.735425	\N	0.95	2025-11-05 21:31:58.187307	f
2e5fdd40-c250-4aa0-b74e-4c4962e72954	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	FaasKeppel	all-rounder	25	2025-11-05 20:28:22.433076	f	\N	{"matches": 1, "runs": 92, "batting_avg": 9.2, "strike_rate": 0.0, "wickets": 27, "bowling_avg": 25.48, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_692	2025-11-05 20:28:22.433224	2025-11-06 09:28:58.735425	\N	0.96	2025-11-05 21:31:58.18731	f
2f5310d1-ea74-4fcf-97af-ad5b7fbac78d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	MuhammedAsif	all-rounder	25	2025-11-05 20:28:22.602035	f	\N	{"matches": 1, "runs": 140, "batting_avg": 14.0, "strike_rate": 0.0, "wickets": 10, "bowling_avg": 32.2, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_617	2025-11-05 20:28:22.602179	2025-11-06 09:28:58.735426	\N	1.36	2025-11-05 21:31:58.187312	f
2fb11813-bd3d-4809-903c-57230560c1de	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	AhmerAli	bowler	25	2025-11-05 20:28:22.748053	f	\N	{"matches": 2, "runs": 26, "batting_avg": 3.25, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 29.83, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_629	2025-11-05 20:28:22.748198	2025-11-06 09:28:58.735426	\N	3.67	2025-11-05 21:31:58.187314	f
301a8d5a-bb31-4112-b1f1-7675da44c1e5	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	SitheshVigneshwaran	all-rounder	25	2025-11-05 20:28:22.36691	f	\N	{"matches": 2, "runs": 352, "batting_avg": 18.53, "strike_rate": 0.0, "wickets": 28, "bowling_avg": 22.64, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_296	2025-11-05 20:28:22.367066	2025-11-06 09:28:58.735426	\N	0.91	2025-11-05 21:31:58.187315	f
314e8276-3847-4a67-83b1-96e168539108	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	BhupendraSingh	bowler	25	2025-11-05 20:28:22.78468	f	\N	{"matches": 3, "runs": 22, "batting_avg": 7.33, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 31.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_451	2025-11-05 20:28:22.784837	2025-11-06 09:28:58.735426	\N	4.17	2025-11-05 21:31:58.18732	f
3197ac32-9321-4007-936c-f43849bcf8ba	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	NageshwarDanturti	batsman	25	2025-11-05 20:28:22.429276	f	\N	{"matches": 14, "runs": 226, "batting_avg": 25.11, "strike_rate": 0.0, "wickets": 21, "bowling_avg": 24.52, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_071	2025-11-05 20:28:22.42946	2025-11-06 09:28:58.735426	\N	0.95	2025-11-05 21:31:58.187321	f
31ca0c0e-315e-4346-96d2-a2a2c00032f2	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	PuneetBindlish	all-rounder	25	2025-11-05 20:28:22.371854	f	\N	{"matches": 2, "runs": 545, "batting_avg": 41.92, "strike_rate": 0.0, "wickets": 18, "bowling_avg": 26.28, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_051	2025-11-05 20:28:22.372023	2025-11-06 09:28:58.735427	\N	0.9	2025-11-05 21:31:58.187323	f
32109804-5ec6-4f40-a311-6afde507223c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	ShahrukhMahmood	all-rounder	25	2025-11-05 20:28:22.759165	f	\N	{"matches": 1, "runs": 34, "batting_avg": 6.8, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 43.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_437	2025-11-05 20:28:22.75931	2025-11-06 09:28:58.735427	\N	3.82	2025-11-05 21:31:58.187329	f
3326afa6-9646-426e-b5fe-d12263fbb215	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	ShahaanAnwar	all-rounder	25	2025-11-05 20:28:22.70106	f	\N	{"matches": 1, "runs": 87, "batting_avg": 8.7, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 30.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_467	2025-11-05 20:28:22.701219	2025-11-06 09:28:58.735427	\N	3.01	2025-11-05 21:31:58.187333	f
333348f5-926c-4c79-9121-bd8d91860319	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	UjjawalRanjan	all-rounder	25	2025-11-05 20:28:22.349386	f	\N	{"matches": 2, "runs": 533, "batting_avg": 26.65, "strike_rate": 0.0, "wickets": 25, "bowling_avg": 16.92, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_018	2025-11-05 20:28:22.349542	2025-11-06 09:28:58.735427	\N	0.88	2025-11-05 21:31:58.187334	f
33625b79-4a50-4ce9-a6af-1d74fea662a3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	AnkushTrikha	batsman	25	2025-11-05 20:28:22.824738	f	\N	{"matches": 6, "runs": 60, "batting_avg": 12.0, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_076	2025-11-05 20:28:22.825023	2025-11-06 09:28:58.735427	\N	4.42	2025-11-05 21:31:58.187337	f
33aafe40-9ecf-407a-ac21-8d6184c28d15	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	HimanshuPaliwal	all-rounder	25	2025-11-05 20:28:22.48921	f	\N	{"matches": 2, "runs": 223, "batting_avg": 22.3, "strike_rate": 0.0, "wickets": 15, "bowling_avg": 22.33, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_146	2025-11-05 20:28:22.489357	2025-11-06 09:28:58.735428	\N	0.97	2025-11-05 21:31:58.187339	f
34fb5bc5-3efe-490e-a382-443e8b132cb8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	AqibSaleem	all-rounder	25	2025-11-05 20:28:22.466205	f	\N	{"matches": 1, "runs": 320, "batting_avg": 29.09, "strike_rate": 0.0, "wickets": 13, "bowling_avg": 38.31, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_652	2025-11-05 20:28:22.466352	2025-11-06 09:28:58.735428	\N	0.96	2025-11-05 21:31:58.187341	f
35b0a219-6aaa-4903-bb76-24b70bfa2678	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	SharadDonga	batsman	25	2025-11-05 20:28:22.725167	f	\N	{"matches": 1, "runs": 170, "batting_avg": 11.33, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_708	2025-11-05 20:28:22.725322	2025-11-06 09:28:58.735428	\N	2.95	2025-11-05 21:31:58.187345	f
3657e01f-4766-42fd-9f2f-6667897d3cb5	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	CarlGilding	batsman	25	2025-11-05 20:28:22.74124	f	\N	{"matches": 1, "runs": 156, "batting_avg": 15.6, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_666	2025-11-05 20:28:22.741404	2025-11-06 09:28:58.735428	\N	3.15	2025-11-05 21:31:58.187346	f
3770207e-302d-44cc-8b7f-c8e78330fdaa	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	MahediMridul	all-rounder	25	2025-11-05 20:28:22.344416	f	\N	{"matches": 2, "runs": 757, "batting_avg": 34.41, "strike_rate": 0.0, "wickets": 17, "bowling_avg": 23.47, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_085	2025-11-05 20:28:22.344584	2025-11-06 09:28:58.735428	\N	0.86	2025-11-05 21:31:58.187351	f
37d4e6d7-122b-4992-9dc5-399e775d96d5	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	RohitKapoor	batsman	25	2025-11-05 20:28:22.527747	f	\N	{"matches": 6, "runs": 269, "batting_avg": 29.89, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 15.78, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_055	2025-11-05 20:28:22.527908	2025-11-06 09:28:58.735429	\N	0.98	2025-11-05 21:31:58.187352	f
38e881f7-a5ca-4be0-b29c-27c0aebef1c6	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	PrasukJain	all-rounder	25	2025-11-05 20:28:22.376432	f	\N	{"matches": 1, "runs": 423, "batting_avg": 32.54, "strike_rate": 0.0, "wickets": 23, "bowling_avg": 17.78, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_567	2025-11-05 20:28:22.37659	2025-11-06 09:28:58.735429	\N	0.91	2025-11-05 21:31:58.187355	f
398e41b4-a2d6-4faf-a80a-02c32bbd0520	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	AylinJoe	all-rounder	25	2025-11-05 20:28:22.545592	f	\N	{"matches": 1, "runs": 130, "batting_avg": 7.65, "strike_rate": 0.0, "wickets": 14, "bowling_avg": 32.43, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_577	2025-11-05 20:28:22.545742	2025-11-06 09:28:58.735429	\N	0.99	2025-11-05 21:31:58.187357	f
39fabd28-1713-4a59-8922-04b1ea36a334	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	ZakQureshi	batsman	25	2025-11-05 20:28:22.736286	f	\N	{"matches": 1, "runs": 157, "batting_avg": 26.17, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_461	2025-11-05 20:28:22.73644	2025-11-06 09:28:58.735429	\N	3.14	2025-11-05 21:31:58.18736	f
3a9e0fef-f369-43f9-a721-85a043678f51	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	ShreyasSinha	batsman	25	2025-11-05 20:28:22.713521	f	\N	{"matches": 1, "runs": 154, "batting_avg": 19.25, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 87.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_200	2025-11-05 20:28:22.713669	2025-11-06 09:28:58.735429	\N	2.86	2025-11-05 21:31:58.187363	f
3b38711c-99e4-4c16-8488-8be214b9ddbf	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	SandeepChavali	all-rounder	25	2025-11-05 20:28:22.445273	f	\N	{"matches": 4, "runs": 194, "batting_avg": 21.56, "strike_rate": 0.0, "wickets": 21, "bowling_avg": 23.62, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_030	2025-11-05 20:28:22.44543	2025-11-06 09:28:58.73543	\N	0.96	2025-11-05 21:31:58.187365	f
3cd42d6e-027d-4b3f-bccf-c9939051c66a	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	KamalMahana	bowler	25	2025-11-05 20:28:22.665416	f	\N	{"matches": 1, "runs": 18, "batting_avg": 6.0, "strike_rate": 0.0, "wickets": 10, "bowling_avg": 10.8, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_535	2025-11-05 20:28:22.665562	2025-11-06 09:28:58.73543	\N	2.82	2025-11-05 21:31:58.187366	f
3d07f68f-143f-48be-a5fa-084f27e1aa44	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	ParthaBhattacharjee	batsman	25	2025-11-05 20:28:22.712676	f	\N	{"matches": 2, "runs": 184, "batting_avg": 20.44, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_274	2025-11-05 20:28:22.712838	2025-11-06 09:28:58.73543	\N	2.75	2025-11-05 21:31:58.187368	f
3d0c09cb-ed15-41c0-b1a7-7e143115cb11	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	OscarGrawe	batsman	25	2025-11-05 20:28:22.834608	f	\N	{"matches": 3, "runs": 33, "batting_avg": 8.25, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 26.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_084	2025-11-05 20:28:22.834783	2025-11-06 09:28:58.73543	\N	4.54	2025-11-05 21:31:58.187369	f
3e17c600-2d6a-4f62-9bcf-7f5ecd24d93d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	NavinSaran	all-rounder	25	2025-11-05 20:28:22.399483	f	\N	{"matches": 5, "runs": 448, "batting_avg": 40.73, "strike_rate": 0.0, "wickets": 16, "bowling_avg": 21.88, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_016	2025-11-05 20:28:22.399632	2025-11-06 09:28:58.73543	\N	0.93	2025-11-05 21:31:58.187373	f
3e512524-d50a-4fbf-bcd3-d9cc223f0cf0	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	SauravSharma	batsman	25	2025-11-05 20:28:22.840886	f	\N	{"matches": 1, "runs": 19, "batting_avg": 9.5, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 30.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_698	2025-11-05 20:28:22.841114	2025-11-06 09:28:58.73543	\N	4.67	2025-11-05 21:31:58.187375	f
3f75101c-a5e7-48c9-8682-4ed3ae772ac1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	AhmedMirzada	all-rounder	25	2025-11-05 20:28:22.422909	f	\N	{"matches": 2, "runs": 159, "batting_avg": 12.23, "strike_rate": 0.0, "wickets": 25, "bowling_avg": 20.12, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_337	2025-11-05 20:28:22.423074	2025-11-06 09:28:58.735431	\N	0.95	2025-11-05 21:31:58.187379	f
3ff19e3f-dbb4-4227-a578-9dd0b39dadfe	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	TayubTabassum	batsman	25	2025-11-05 20:28:22.538568	f	\N	{"matches": 1, "runs": 415, "batting_avg": 29.64, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_662	2025-11-05 20:28:22.538716	2025-11-06 09:28:58.735431	\N	0.98	2025-11-05 21:31:58.187387	f
4036b7db-da83-4239-923c-75bedc96b8dd	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	MohammedShabir	batsman	25	2025-11-05 20:28:22.800461	f	\N	{"matches": 2, "runs": 82, "batting_avg": 7.45, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_322	2025-11-05 20:28:22.800622	2025-11-06 09:28:58.735431	\N	4.17	2025-11-05 21:31:58.187391	f
4097ad2b-5cb3-4251-84eb-37d717b34320	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	JacoFourie	all-rounder	25	2025-11-05 20:28:22.321782	f	\N	{"matches": 2, "runs": 854, "batting_avg": 42.7, "strike_rate": 0.0, "wickets": 34, "bowling_avg": 20.12, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_111	2025-11-05 20:28:22.322068	2025-11-06 09:28:58.735432	\N	0.79	2025-11-05 21:31:58.187392	f
41d83a2a-b52c-4719-879e-c3cb54782b73	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	AbadSethi	all-rounder	25	2025-11-05 20:28:22.726104	f	\N	{"matches": 1, "runs": 86, "batting_avg": 17.2, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 29.2, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_262	2025-11-05 20:28:22.726254	2025-11-06 09:28:58.735432	\N	3.26	2025-11-05 21:31:58.187396	f
41e9b774-6317-456a-b83b-e25674549bae	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	MarcKerdijk	batsman	25	2025-11-05 20:28:22.757317	f	\N	{"matches": 1, "runs": 129, "batting_avg": 12.9, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_368	2025-11-05 20:28:22.757461	2025-11-06 09:28:58.735432	\N	3.54	2025-11-05 21:31:58.187398	f
42c18fe4-ea1c-4bb6-a04f-0504657d557b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	NavjotSingh	bowler	25	2025-11-05 20:28:22.403996	f	\N	{"matches": 2, "runs": 34, "batting_avg": 4.25, "strike_rate": 0.0, "wickets": 34, "bowling_avg": 20.26, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_109	2025-11-05 20:28:22.404139	2025-11-06 09:28:58.735432	\N	0.95	2025-11-05 21:31:58.187401	f
44b0ce31-547d-480b-89b3-05cabb660912	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	ClaudioPucciatti	all-rounder	25	2025-11-05 20:28:22.644843	f	\N	{"matches": 1, "runs": 103, "batting_avg": 8.58, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 27.11, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_351	2025-11-05 20:28:22.645004	2025-11-06 09:28:58.735433	\N	2.13	2025-11-05 21:31:58.187411	f
4539e023-4fa2-449d-8e0f-b61e5222ba07	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	ArslanAhmed	batsman	25	2025-11-05 20:28:22.394762	f	\N	{"matches": 13, "runs": 402, "batting_avg": 28.71, "strike_rate": 0.0, "wickets": 19, "bowling_avg": 20.26, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_021	2025-11-05 20:28:22.394931	2025-11-06 09:28:58.735433	\N	0.93	2025-11-05 21:31:58.187412	f
45cc83dd-2c67-4780-8c98-6a3abd7f6507	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	YugVatsa	bowler	25	2025-11-05 20:28:22.708628	f	\N	{"matches": 1, "runs": 24, "batting_avg": 6.0, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 15.88, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_494	2025-11-05 20:28:22.708771	2025-11-06 09:28:58.735433	\N	3.22	2025-11-05 21:31:58.187418	f
460dbb47-603a-4ea5-b0cc-35487f45ec41	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	VijayaJayanthi	batsman	25	2025-11-05 20:28:22.660222	f	\N	{"matches": 1, "runs": 231, "batting_avg": 21.0, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_221	2025-11-05 20:28:22.660366	2025-11-06 09:28:58.735433	\N	2.07	2025-11-05 21:31:58.187422	f
476ac7bc-f136-4bc4-bd9a-95b3ac4e3be8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	YuyutsuUrs	all-rounder	25	2025-11-05 20:28:22.42606	f	\N	{"matches": 3, "runs": 257, "batting_avg": 18.36, "strike_rate": 0.0, "wickets": 20, "bowling_avg": 24.45, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_266	2025-11-05 20:28:22.426213	2025-11-06 09:28:58.735433	\N	0.95	2025-11-05 21:31:58.187424	f
47d755c2-3fe3-4d0f-9ecf-6e0e278b6da1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	SurajBelavadi	batsman	25	2025-11-05 20:28:22.539458	f	\N	{"matches": 7, "runs": 354, "batting_avg": 22.13, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 44.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_232	2025-11-05 20:28:22.539603	2025-11-06 09:28:58.735434	\N	0.98	2025-11-05 21:31:58.187426	f
48700242-ad94-45b8-a9cf-5ff1402ab9de	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	RahilAhmed	batsman	25	2025-11-05 20:28:22.458992	f	\N	{"matches": 1, "runs": 572, "batting_avg": 24.87, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 39.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_201	2025-11-05 20:28:22.45914	2025-11-06 09:28:58.735434	\N	0.95	2025-11-05 21:31:58.187427	f
48b29f32-a13e-4381-b34d-b4146942a972	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	AkshayaSripatnala	bowler	25	2025-11-05 20:28:22.71445	f	\N	{"matches": 5, "runs": 48, "batting_avg": 5.33, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 36.14, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_105	2025-11-05 20:28:22.714595	2025-11-06 09:28:58.735434	\N	3.23	2025-11-05 21:31:58.187429	f
490a1b6f-4b91-4ce7-8faf-0e003d5f8e42	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	LokeshKumar	batsman	25	2025-11-05 20:28:22.561284	f	\N	{"matches": 2, "runs": 386, "batting_avg": 22.71, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_220	2025-11-05 20:28:22.561428	2025-11-06 09:28:58.735434	\N	0.98	2025-11-05 21:31:58.187431	f
49c2ff3d-1f59-4058-ac8e-28d55c5c0095	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	IsmatullahNasery	bowler	25	2025-11-05 20:28:22.39162	f	\N	{"matches": 2, "runs": 24, "batting_avg": 2.18, "strike_rate": 0.0, "wickets": 37, "bowling_avg": 15.92, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_126	2025-11-05 20:28:22.391784	2025-11-06 09:28:58.735435	\N	0.94	2025-11-05 21:31:58.187435	f
4a1edcfc-4dc6-477a-b55f-565e397ac9a6	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	AbhiAnand	all-rounder	25	2025-11-05 20:28:22.543738	f	\N	{"matches": 1, "runs": 135, "batting_avg": 9.64, "strike_rate": 0.0, "wickets": 14, "bowling_avg": 18.36, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_132	2025-11-05 20:28:22.543902	2025-11-06 09:28:58.735435	\N	0.99	2025-11-05 21:31:58.187438	f
4a72f0b2-3c80-4826-81da-75902460d73e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	LakshaySharma	bowler	25	2025-11-05 20:28:22.682428	f	\N	{"matches": 1, "runs": 21, "batting_avg": 4.2, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 15.67, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_434	2025-11-05 20:28:22.682715	2025-11-06 09:28:58.735435	\N	3.02	2025-11-05 21:31:58.18744	f
4a83a744-3307-460f-aa8a-d70f13b34564	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	RohanSolanki	batsman	25	2025-11-05 20:28:22.622667	f	\N	{"matches": 1, "runs": 300, "batting_avg": 25.0, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_456	2025-11-05 20:28:22.622811	2025-11-06 09:28:58.735435	\N	1.07	2025-11-05 21:31:58.187441	f
4a98a7d1-09c1-4e21-a565-7138c0c25ee0	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	FaisalAbbas	all-rounder	25	2025-11-05 20:28:22.465369	f	\N	{"matches": 1, "runs": 214, "batting_avg": 17.83, "strike_rate": 0.0, "wickets": 18, "bowling_avg": 25.78, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_579	2025-11-05 20:28:22.465513	2025-11-06 09:28:58.735435	\N	0.97	2025-11-05 21:31:58.187443	f
4afb6fb3-ca24-4a2b-9ee4-0aad59c652a4	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	NoudWijnstra	batsman	25	2025-11-05 20:28:22.833433	f	\N	{"matches": 1, "runs": 34, "batting_avg": 5.67, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 93.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_359	2025-11-05 20:28:22.833628	2025-11-06 09:28:58.735436	\N	4.53	2025-11-05 21:31:58.187444	f
4b3b6a07-1631-421e-a3e3-9beb9f8c7624	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	MalyarSafi	bowler	25	2025-11-05 20:28:22.369948	f	\N	{"matches": 17, "runs": 162, "batting_avg": 18.0, "strike_rate": 0.0, "wickets": 36, "bowling_avg": 18.33, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_009	2025-11-05 20:28:22.370113	2025-11-06 09:28:58.735436	\N	0.92	2025-11-05 21:31:58.187446	f
4c4152c5-9069-4078-ad38-46aa38bc91bf	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	RandheerPonnamkunnath	all-rounder	25	2025-11-05 20:28:22.461026	f	\N	{"matches": 1, "runs": 164, "batting_avg": 20.5, "strike_rate": 0.0, "wickets": 21, "bowling_avg": 15.43, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_609	2025-11-05 20:28:22.46117	2025-11-06 09:28:58.735436	\N	0.97	2025-11-05 21:31:58.187453	f
4c682971-b238-436c-933b-da65394f69eb	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	KiranSiripuram	batsman	25	2025-11-05 20:28:22.858858	f	\N	{"matches": 1, "runs": 7, "batting_avg": 3.5, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_533	2025-11-05 20:28:22.859046	2025-11-06 09:28:58.735436	\N	4.94	2025-11-05 21:31:58.187455	f
4da27741-4e56-4573-b68b-5ef610228e24	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	RobineRijke	all-rounder	25	2025-11-05 20:28:22.463731	f	\N	{"matches": 1, "runs": 473, "batting_avg": 23.65, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 15.83, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_532	2025-11-05 20:28:22.463891	2025-11-06 09:28:58.735436	\N	0.95	2025-11-05 21:31:58.187458	f
4dc476b8-3c39-4c40-8c51-877bb917c534	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	ZahraJankie	all-rounder	25	2025-11-05 20:28:22.674618	f	\N	{"matches": 2, "runs": 61, "batting_avg": 7.63, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 36.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_106	2025-11-05 20:28:22.674778	2025-11-06 09:28:58.735437	\N	2.85	2025-11-05 21:31:58.18746	f
4dd10796-86fe-413f-b13b-564f34125d36	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	MuhammadTaha	all-rounder	25	2025-11-05 20:28:22.525004	f	\N	{"matches": 1, "runs": 197, "batting_avg": 14.07, "strike_rate": 0.0, "wickets": 13, "bowling_avg": 32.31, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_074	2025-11-05 20:28:22.525159	2025-11-06 09:28:58.735437	\N	0.98	2025-11-05 21:31:58.187461	f
4ed499a1-a080-4e95-b8c2-5fc1725fe07a	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	ShayanAhmed	bowler	25	2025-11-05 20:28:22.716161	f	\N	{"matches": 2, "runs": 13, "batting_avg": 4.33, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 20.25, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_280	2025-11-05 20:28:22.716304	2025-11-06 09:28:58.735437	\N	3.33	2025-11-05 21:31:58.187464	f
4ef64320-6c27-401b-86da-213b30d58be7	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	LotteHeerkens	bowler	25	2025-11-05 20:28:22.756401	f	\N	{"matches": 6, "runs": 11, "batting_avg": 3.67, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 39.33, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_387	2025-11-05 20:28:22.756545	2025-11-06 09:28:58.735437	\N	3.81	2025-11-05 21:31:58.187466	f
4f21f7aa-c34d-4d64-a90d-86a204f91af9	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	FraserLord	bowler	25	2025-11-05 20:28:22.807849	f	\N	{"matches": 7, "runs": 17, "batting_avg": 2.43, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 52.67, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_268	2025-11-05 20:28:22.808047	2025-11-06 09:28:58.735437	\N	4.37	2025-11-05 21:31:58.187467	f
4f6a2f8f-0e26-41f2-aed4-71de6d654c5e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	GunjanJamindar	all-rounder	25	2025-11-05 20:28:22.466973	f	\N	{"matches": 2, "runs": 339, "batting_avg": 33.9, "strike_rate": 0.0, "wickets": 12, "bowling_avg": 12.17, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_412	2025-11-05 20:28:22.467127	2025-11-06 09:28:58.735438	\N	0.96	2025-11-05 21:31:58.187469	f
4f8cd1c9-e6bf-43a4-a5be-a3f622be363c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	RajanThavaratnam	all-rounder	25	2025-11-05 20:28:22.409308	f	\N	{"matches": 1, "runs": 220, "batting_avg": 16.92, "strike_rate": 0.0, "wickets": 25, "bowling_avg": 21.76, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_307	2025-11-05 20:28:22.409457	2025-11-06 09:28:58.735438	\N	0.94	2025-11-05 21:31:58.187475	f
0221fac8-2e6c-4bbc-9ea4-0d67ccb75b1f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	MithunAjith	all-rounder	25	2025-11-05 20:28:22.73092	f	\N	{"matches": 1, "runs": 52, "batting_avg": 13.0, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 16.67, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_501	2025-11-05 20:28:22.731064	2025-11-06 09:28:58.735395	\N	3.42	2025-11-05 21:31:58.187039	f
5028f8a4-0e0b-467e-8909-dff01013a9b0	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	LuckyPrince	all-rounder	25	2025-11-05 20:28:22.365899	f	\N	{"matches": 1, "runs": 417, "batting_avg": 29.79, "strike_rate": 0.0, "wickets": 25, "bowling_avg": 22.64, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_622	2025-11-05 20:28:22.366056	2025-11-06 09:28:58.735438	\N	0.9	2025-11-05 21:31:58.187479	f
503b551f-7fa4-4798-bc71-21153f6df024	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	AdeelMasih	batsman	25	2025-11-05 20:28:22.723361	f	\N	{"matches": 1, "runs": 143, "batting_avg": 17.88, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 64.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_595	2025-11-05 20:28:22.723507	2025-11-06 09:28:58.735438	\N	3.02	2025-11-05 21:31:58.18748	f
515a0515-d797-4703-be21-073bc8e55b3d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	AniketBhattacharya	bowler	25	2025-11-05 20:28:22.814607	f	\N	{"matches": 2, "runs": 6, "batting_avg": 2.0, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 50.33, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_503	2025-11-05 20:28:22.81478	2025-11-06 09:28:58.735438	\N	4.48	2025-11-05 21:31:58.187486	f
51ecccfc-094c-43f6-baee-cec556829beb	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	VishalKumar	all-rounder	25	2025-11-05 20:28:22.355081	f	\N	{"matches": 3, "runs": 207, "batting_avg": 9.41, "strike_rate": 0.0, "wickets": 38, "bowling_avg": 34.37, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_061	2025-11-05 20:28:22.355237	2025-11-06 09:28:58.735439	\N	0.9	2025-11-05 21:31:58.187489	f
522fd27e-0e32-4161-a1d4-65cb89751d93	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	AnityaAnand	all-rounder	25	2025-11-05 20:28:22.596552	f	\N	{"matches": 1, "runs": 79, "batting_avg": 9.88, "strike_rate": 0.0, "wickets": 13, "bowling_avg": 25.23, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_550	2025-11-05 20:28:22.596695	2025-11-06 09:28:58.735439	\N	1.49	2025-11-05 21:31:58.187491	f
52c8116b-435d-4255-9f9b-5721819cf2ae	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	KandeeNageswaran	batsman	25	2025-11-05 20:28:22.82668	f	\N	{"matches": 1, "runs": 60, "batting_avg": 10.0, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_603	2025-11-05 20:28:22.82692	2025-11-06 09:28:58.735439	\N	4.42	2025-11-05 21:31:58.187495	f
53a18614-d323-4161-bcab-b9ca109819a3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	MuswarAhmad	all-rounder	25	2025-11-05 20:28:22.695123	f	\N	{"matches": 1, "runs": 97, "batting_avg": 9.7, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 64.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_417	2025-11-05 20:28:22.695272	2025-11-06 09:28:58.735439	\N	2.9	2025-11-05 21:31:58.187497	f
54c78cac-3282-4f65-a678-6b7a61ee83ac	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	VetrivelanKarunanithi	all-rounder	25	2025-11-05 20:28:22.607417	f	\N	{"matches": 1, "runs": 110, "batting_avg": 36.67, "strike_rate": 0.0, "wickets": 11, "bowling_avg": 21.09, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_704	2025-11-05 20:28:22.60756	2025-11-06 09:28:58.735439	\N	1.56	2025-11-05 21:31:58.1875	f
55bdde68-6553-4525-958f-ae86b49c3858	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	QudratullahAkbari	all-rounder	25	2025-11-05 20:28:22.60473	f	\N	{"matches": 1, "runs": 37, "batting_avg": 7.4, "strike_rate": 0.0, "wickets": 14, "bowling_avg": 29.21, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_169	2025-11-05 20:28:22.604888	2025-11-06 09:28:58.73544	\N	1.71	2025-11-05 21:31:58.187503	f
56a193c6-cb96-4d4b-b123-7d457ae4124e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	DhruvSogani	batsman	25	2025-11-05 20:28:22.775107	f	\N	{"matches": 1, "runs": 77, "batting_avg": 19.25, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 40.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_436	2025-11-05 20:28:22.77528	2025-11-06 09:28:58.73544	\N	3.91	2025-11-05 21:31:58.187505	f
5707d16c-4335-496d-a081-0278874c6434	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	UdaySharma	bowler	25	2025-11-05 20:28:22.606525	f	\N	{"matches": 2, "runs": 32, "batting_avg": 8.0, "strike_rate": 0.0, "wickets": 14, "bowling_avg": 31.57, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_214	2025-11-05 20:28:22.606669	2025-11-06 09:28:58.73544	\N	1.76	2025-11-05 21:31:58.187507	f
588df776-bcb6-4e7f-8102-6c05d823835f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	DevanshuUke	all-rounder	25	2025-11-05 20:28:22.659328	f	\N	{"matches": 1, "runs": 131, "batting_avg": 10.92, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 17.33, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_601	2025-11-05 20:28:22.659474	2025-11-06 09:28:58.73544	\N	2.42	2025-11-05 21:31:58.187519	f
58c99648-813a-4170-8710-6bf65dcffaff	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	ArifienHayat	bowler	25	2025-11-05 20:28:22.71171	f	\N	{"matches": 2, "runs": 23, "batting_avg": 5.75, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 30.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_645	2025-11-05 20:28:22.711863	2025-11-06 09:28:58.73544	\N	3.23	2025-11-05 21:31:58.187521	f
592c3ba3-c7fb-4194-82f0-35817714cf4c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	TamilArasu	batsman	25	2025-11-05 20:28:22.587539	f	\N	{"matches": 2, "runs": 287, "batting_avg": 15.94, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 68.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_316	2025-11-05 20:28:22.587685	2025-11-06 09:28:58.735441	\N	0.99	2025-11-05 21:31:58.187526	f
59e4891d-1a28-4877-924e-f4eb6769d4fc	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	ShrihanChakrabarty	bowler	25	2025-11-05 20:28:22.83813	f	\N	{"matches": 1, "runs": 4, "batting_avg": 2.0, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 36.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_699	2025-11-05 20:28:22.838297	2025-11-06 09:28:58.735441	\N	4.65	2025-11-05 21:31:58.18753	f
5a8d0654-4acd-4f23-9ed0-c7fcbadd04a8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	WaheedullahSafi	all-rounder	25	2025-11-05 20:28:22.38601	f	\N	{"matches": 2, "runs": 225, "batting_avg": 16.07, "strike_rate": 0.0, "wickets": 30, "bowling_avg": 27.43, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_496	2025-11-05 20:28:22.386158	2025-11-06 09:28:58.735441	\N	0.93	2025-11-05 21:31:58.187533	f
a7a3f602-01ee-4a75-ad0a-9e6274c1693f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	DaanVierling	batsman	25	2025-11-05 20:28:22.396686	f	\N	{"matches": 1, "runs": 752, "batting_avg": 30.08, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 29.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_700	2025-11-05 20:28:22.396847	2025-11-06 10:09:45.309387	\N	0.91	2025-11-05 21:31:58.187987	t
5a90d219-0ebd-411b-b1ad-08f3fc85083c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	MaxwellGorlee	all-rounder	25	2025-11-05 20:28:22.761947	f	\N	{"matches": 1, "runs": 58, "batting_avg": 7.25, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 31.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_115	2025-11-05 20:28:22.762092	2025-11-06 09:28:58.735441	\N	3.81	2025-11-05 21:31:58.187534	f
5aafd0c8-8ab3-4df5-ac39-014e239f6e6c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	DihanBekker	all-rounder	25	2025-11-05 20:28:22.403097	f	\N	{"matches": 2, "runs": 294, "batting_avg": 29.4, "strike_rate": 0.0, "wickets": 23, "bowling_avg": 18.7, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_299	2025-11-05 20:28:22.403245	2025-11-06 09:28:58.735442	\N	0.93	2025-11-05 21:31:58.187536	f
5c355aa0-2d53-495e-b394-ab4412f80ce1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	AdityaBura	all-rounder	25	2025-11-05 20:28:22.334299	f	\N	{"matches": 2, "runs": 886, "batting_avg": 25.31, "strike_rate": 0.0, "wickets": 18, "bowling_avg": 26.67, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_317	2025-11-05 20:28:22.334475	2025-11-06 09:28:58.735442	\N	0.84	2025-11-05 21:31:58.187543	f
5dc1fffc-43c2-4342-9f44-c6bf50320bd3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	AmitozBindra	all-rounder	25	2025-11-05 20:28:22.522139	f	\N	{"matches": 1, "runs": 204, "batting_avg": 22.67, "strike_rate": 0.0, "wickets": 13, "bowling_avg": 24.54, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_653	2025-11-05 20:28:22.522282	2025-11-06 09:28:58.735442	\N	0.98	2025-11-05 21:31:58.187551	f
5efdc5f2-3927-4d82-a05e-76cf7f08c317	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	TimVersteegh	all-rounder	25	2025-11-05 20:28:22.363194	f	\N	{"matches": 2, "runs": 333, "batting_avg": 25.62, "strike_rate": 0.0, "wickets": 30, "bowling_avg": 21.8, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_031	2025-11-05 20:28:22.363346	2025-11-06 09:28:58.735442	\N	0.91	2025-11-05 21:31:58.187553	f
5fcb6e12-6c8d-4e69-974e-21a2a765bdfe	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	KamranNasir	all-rounder	25	2025-11-05 20:28:22.46283	f	\N	{"matches": 1, "runs": 135, "batting_avg": 9.64, "strike_rate": 0.0, "wickets": 22, "bowling_avg": 30.05, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_313	2025-11-05 20:28:22.462995	2025-11-06 09:28:58.735443	\N	0.97	2025-11-05 21:31:58.187554	f
5fed357e-f8ee-415a-bf3f-bcdb18276761	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	IrfanFarroq	all-rounder	25	2025-11-05 20:28:22.497995	f	\N	{"matches": 1, "runs": 211, "batting_avg": 35.17, "strike_rate": 0.0, "wickets": 15, "bowling_avg": 20.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_343	2025-11-05 20:28:22.49814	2025-11-06 09:28:58.735443	\N	0.98	2025-11-05 21:31:58.187556	f
60a19728-352b-429c-b734-e6d8fe3e4dab	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	NileshLohia	batsman	25	2025-11-05 20:28:22.764686	f	\N	{"matches": 1, "runs": 121, "batting_avg": 13.44, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_358	2025-11-05 20:28:22.764831	2025-11-06 09:28:58.735443	\N	3.66	2025-11-05 21:31:58.187559	f
611636f7-2f36-41ea-a672-1afbb5e6ae3c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	AshokDangi	bowler	25	2025-11-05 20:28:22.59934	f	\N	{"matches": 1, "runs": 16, "batting_avg": 4.0, "strike_rate": 0.0, "wickets": 15, "bowling_avg": 21.67, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_545	2025-11-05 20:28:22.599485	2025-11-06 09:28:58.735443	\N	1.68	2025-11-05 21:31:58.187564	f
61682d04-14eb-4e2a-be57-4f8fe18e1f93	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	FaizanQureshi	batsman	25	2025-11-05 20:28:22.705163	f	\N	{"matches": 1, "runs": 159, "batting_avg": 14.45, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 72.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_364	2025-11-05 20:28:22.705327	2025-11-06 09:28:58.735443	\N	2.79	2025-11-05 21:31:58.187574	f
61b90ea8-b14b-4212-bcd0-82080d851df1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	AbdulmananMian	bowler	25	2025-11-05 20:28:22.8477	f	\N	{"matches": 1, "runs": 6, "batting_avg": 6.0, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 109.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_548	2025-11-05 20:28:22.847867	2025-11-06 09:28:58.735444	\N	4.79	2025-11-05 21:31:58.187576	f
623846b7-500a-42e6-b411-1210f30ff888	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	KokabNadeem	batsman	25	2025-11-05 20:28:22.550375	f	\N	{"matches": 1, "runs": 368, "batting_avg": 21.65, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 13.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_119	2025-11-05 20:28:22.550525	2025-11-06 09:28:58.735444	\N	0.98	2025-11-05 21:31:58.187578	f
6244b595-03e6-46d4-b5c9-4905320db6ba	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	SeanRyan	bowler	25	2025-11-05 20:28:22.798435	f	\N	{"matches": 4, "runs": 7, "batting_avg": 2.33, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 17.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_636	2025-11-05 20:28:22.798594	2025-11-06 09:28:58.735444	\N	4.31	2025-11-05 21:31:58.187579	f
631b30e0-8a06-4713-a43d-c6afbc38db22	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	AbhipreetSinha	batsman	25	2025-11-05 20:28:22.812341	f	\N	{"matches": 2, "runs": 68, "batting_avg": 17.0, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_564	2025-11-05 20:28:22.812509	2025-11-06 09:28:58.735444	\N	4.33	2025-11-05 21:31:58.187583	f
63b0dd2b-b44d-42b3-b2e7-a7fd9c79cc6f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	SaifSaifullah	bowler	25	2025-11-05 20:28:22.480768	f	\N	{"matches": 2, "runs": 26, "batting_avg": 3.71, "strike_rate": 0.0, "wickets": 24, "bowling_avg": 35.63, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_371	2025-11-05 20:28:22.481064	2025-11-06 09:28:58.735444	\N	0.98	2025-11-05 21:31:58.187584	f
64f34602-027b-4ec0-9a16-b6a46fb27bb5	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	PraveenKota	batsman	25	2025-11-05 20:28:22.677395	f	\N	{"matches": 1, "runs": 207, "batting_avg": 17.25, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_592	2025-11-05 20:28:22.677541	2025-11-06 09:28:58.735445	\N	2.42	2025-11-05 21:31:58.187586	f
650ed5fd-ee5a-4a31-8fae-8e4079ff6d81	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	TarunPal	batsman	25	2025-11-05 20:28:22.595662	f	\N	{"matches": 6, "runs": 320, "batting_avg": 26.67, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 36.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_189	2025-11-05 20:28:22.595806	2025-11-06 09:28:58.735445	\N	0.99	2025-11-05 21:31:58.187587	f
656dddb8-b9af-44eb-9cc2-7388d71f966b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	AxayaKansal	bowler	25	2025-11-05 20:28:22.453625	f	\N	{"matches": 10, "runs": 90, "batting_avg": 18.0, "strike_rate": 0.0, "wickets": 25, "bowling_avg": 21.08, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_127	2025-11-05 20:28:22.453775	2025-11-06 09:28:58.735445	\N	0.97	2025-11-05 21:31:58.187589	f
65cca0ec-d618-4ca5-b2b1-92ca20e9902d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	StephenHart	all-rounder	25	2025-11-05 20:28:22.721289	f	\N	{"matches": 1, "runs": 130, "batting_avg": 14.44, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 6.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_282	2025-11-05 20:28:22.72143	2025-11-06 09:28:58.735445	\N	3.05	2025-11-05 21:31:58.187591	f
65dcc9f6-99a2-4e88-8c6d-cf3e423c49dd	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	XanderUdo	batsman	25	2025-11-05 20:28:22.670048	f	\N	{"matches": 6, "runs": 187, "batting_avg": 26.71, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 72.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_288	2025-11-05 20:28:22.670191	2025-11-06 09:28:58.735445	\N	2.39	2025-11-05 21:31:58.187592	f
667808e0-fed9-462e-8a61-a1c87415ef76	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	SahelEzmarai	bowler	25	2025-11-05 20:28:22.782604	f	\N	{"matches": 1, "runs": 27, "batting_avg": 9.0, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 26.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_427	2025-11-05 20:28:22.782764	2025-11-06 09:28:58.735446	\N	4.12	2025-11-05 21:31:58.187596	f
6699917a-f50b-4e7a-9fd8-ae590e5f5987	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	BalramKrishnakumar	all-rounder	25	2025-11-05 20:28:22.639647	f	\N	{"matches": 2, "runs": 126, "batting_avg": 15.75, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 32.13, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_506	2025-11-05 20:28:22.639794	2025-11-06 09:28:58.735446	\N	2.03	2025-11-05 21:31:58.187597	f
66ea5ae2-38ed-4081-b79f-7f8ab6c22b23	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	DakshShah	all-rounder	25	2025-11-05 20:28:22.699039	f	\N	{"matches": 1, "runs": 113, "batting_avg": 11.3, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 38.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_092	2025-11-05 20:28:22.699186	2025-11-06 09:28:58.735446	\N	2.91	2025-11-05 21:31:58.187599	f
66faae16-ff06-44e0-a691-9b3596ef871d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	JagjitSingh	bowler	25	2025-11-05 20:28:22.762857	f	\N	{"matches": 2, "runs": 26, "batting_avg": 3.25, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 35.2, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_138	2025-11-05 20:28:22.763023	2025-11-06 09:28:58.735446	\N	3.9	2025-11-05 21:31:58.1876	f
6728575f-6f71-4475-9d94-553899f6a48d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	NaveenMahaveer	all-rounder	25	2025-11-05 20:28:22.618912	f	\N	{"matches": 1, "runs": 118, "batting_avg": 16.86, "strike_rate": 0.0, "wickets": 10, "bowling_avg": 21.2, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_491	2025-11-05 20:28:22.619064	2025-11-06 09:28:58.735446	\N	1.68	2025-11-05 21:31:58.187602	f
673999a3-0205-4882-89ed-028190df4a1f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	SamEikelenboom	batsman	25	2025-11-05 20:28:22.792213	f	\N	{"matches": 1, "runs": 76, "batting_avg": 9.5, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 187.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_128	2025-11-05 20:28:22.792373	2025-11-06 09:28:58.735446	\N	4.08	2025-11-05 21:31:58.187603	f
677ec853-a72c-44b0-ac03-d8fb5c431434	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	VinayBhat	all-rounder	25	2025-11-05 20:28:22.519463	f	\N	{"matches": 1, "runs": 104, "batting_avg": 11.56, "strike_rate": 0.0, "wickets": 18, "bowling_avg": 33.28, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_600	2025-11-05 20:28:22.519605	2025-11-06 09:28:58.735447	\N	0.99	2025-11-05 21:31:58.187609	f
67859080-005e-446e-9f3f-893f1313cc0e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	AadyaChandra	bowler	25	2025-11-05 20:28:22.787758	f	\N	{"matches": 1, "runs": 19, "batting_avg": 1.73, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 48.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_686	2025-11-05 20:28:22.787937	2025-11-06 09:28:58.735447	\N	4.2	2025-11-05 21:31:58.187613	f
67f1632e-d38b-4ab1-9f9d-63f6e77e7d7c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	SrinivasMuralidharan	bowler	25	2025-11-05 20:28:22.85096	f	\N	{"matches": 1, "runs": 1, "batting_avg": 0.5, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 40.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_646	2025-11-05 20:28:22.851123	2025-11-06 09:28:58.735447	\N	4.84	2025-11-05 21:31:58.187615	f
6826ce38-c99e-42bc-a52d-a5ac98638947	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	ChandrahasUndurti	batsman	25	2025-11-05 20:28:22.830994	f	\N	{"matches": 1, "runs": 37, "batting_avg": 5.29, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 116.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_674	2025-11-05 20:28:22.831226	2025-11-06 09:28:58.735447	\N	4.5	2025-11-05 21:31:58.187616	f
6845e989-bf30-459e-99ac-b6f16cee77bb	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	SunnyKakkar	all-rounder	25	2025-11-05 20:28:22.512483	f	\N	{"matches": 2, "runs": 113, "batting_avg": 37.67, "strike_rate": 0.0, "wickets": 18, "bowling_avg": 13.94, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_546	2025-11-05 20:28:22.512632	2025-11-06 09:28:58.735447	\N	0.99	2025-11-05 21:31:58.187618	f
687a5633-0165-416f-9894-7168feb1d267	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	SadaqatSafi	all-rounder	25	2025-11-05 20:28:22.326657	f	\N	{"matches": 1, "runs": 987, "batting_avg": 42.91, "strike_rate": 0.0, "wickets": 23, "bowling_avg": 29.52, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_478	2025-11-05 20:28:22.326903	2025-11-06 09:28:58.735448	\N	0.8	2025-11-05 21:31:58.18762	f
68dbce94-9929-4a0f-887e-bfbd896dc469	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	KhyatNakhwa	bowler	25	2025-11-05 20:28:22.671843	f	\N	{"matches": 7, "runs": 65, "batting_avg": 16.25, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 22.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_094	2025-11-05 20:28:22.672003	2025-11-06 09:28:58.735448	\N	2.81	2025-11-05 21:31:58.187621	f
693dbd66-ebad-4ee8-bf69-488b8827c5e6	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	AaditNema	all-rounder	25	2025-11-05 20:28:22.767436	f	\N	{"matches": 1, "runs": 49, "batting_avg": 24.5, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 26.25, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_518	2025-11-05 20:28:22.767579	2025-11-06 09:28:58.735449	\N	3.91	2025-11-05 21:31:58.187625	f
69a98d02-599c-4321-8271-435801439b34	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	IbrahimShah	batsman	25	2025-11-05 20:28:22.829508	f	\N	{"matches": 1, "runs": 58, "batting_avg": 7.25, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_230	2025-11-05 20:28:22.829791	2025-11-06 09:28:58.735449	\N	4.45	2025-11-05 21:31:58.187626	f
6a400c40-372f-45ad-b2ed-4d18d749e79b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	SantoshSahoo	all-rounder	25	2025-11-05 20:28:22.625787	f	\N	{"matches": 1, "runs": 149, "batting_avg": 24.83, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 44.13, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_697	2025-11-05 20:28:22.625943	2025-11-06 09:28:58.735449	\N	1.69	2025-11-05 21:31:58.187629	f
6a898ee1-c846-471c-b961-45206f71abac	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	VijayGomatam	batsman	25	2025-11-05 20:28:22.675584	f	\N	{"matches": 8, "runs": 179, "batting_avg": 17.9, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 52.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_107	2025-11-05 20:28:22.67573	2025-11-06 09:28:58.735449	\N	2.5	2025-11-05 21:31:58.187632	f
6a9f8a8a-754b-4574-aa5f-3d8403d0d1c1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	AqilGhadiali	batsman	25	2025-11-05 20:28:22.832238	f	\N	{"matches": 1, "runs": 57, "batting_avg": 9.5, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_197	2025-11-05 20:28:22.832416	2025-11-06 09:28:58.735449	\N	4.46	2025-11-05 21:31:58.187634	f
6abe7809-bda3-4dfa-be94-ba159728f5c8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	BhanpersadSoechit	batsman	25	2025-11-05 20:28:22.842153	f	\N	{"matches": 1, "runs": 40, "batting_avg": 6.67, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_719	2025-11-05 20:28:22.84232	2025-11-06 09:28:58.735449	\N	4.63	2025-11-05 21:31:58.187635	f
6b3ebf6c-a8b2-4008-86b5-0e576a8430e0	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	AmanpreetSingh	bowler	25	2025-11-05 20:28:22.490808	f	\N	{"matches": 12, "runs": 89, "batting_avg": 12.71, "strike_rate": 0.0, "wickets": 21, "bowling_avg": 25.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_025	2025-11-05 20:28:22.490977	2025-11-06 09:28:58.73545	\N	0.98	2025-11-05 21:31:58.187639	f
6bb35e30-7bcc-431d-96a8-2f4f104ce7d2	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	PraneethPendru	all-rounder	25	2025-11-05 20:28:22.451785	f	\N	{"matches": 1, "runs": 243, "batting_avg": 27.0, "strike_rate": 0.0, "wickets": 18, "bowling_avg": 18.28, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_504	2025-11-05 20:28:22.451954	2025-11-06 09:28:58.73545	\N	0.96	2025-11-05 21:31:58.187643	f
6bc6771e-3180-4f47-89d9-d23ddf2c170f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	IHTISHAM HAKRAM	bowler	25	2025-11-05 20:28:22.750844	f	\N	{"matches": 1, "runs": 22, "batting_avg": 2.75, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 38.67, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_373	2025-11-05 20:28:22.751015	2025-11-06 09:28:58.73545	\N	3.7	2025-11-05 21:31:58.187645	f
6be9f920-082e-4c59-bef1-799258121e16	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	REHANMUHAMMAD	all-rounder	25	2025-11-05 20:28:22.374047	f	\N	{"matches": 2, "runs": 478, "batting_avg": 18.38, "strike_rate": 0.0, "wickets": 21, "bowling_avg": 22.9, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_669	2025-11-05 20:28:22.374224	2025-11-06 09:28:58.73545	\N	0.91	2025-11-05 21:31:58.187647	f
6bec67af-c6b2-4aac-a8bc-0913d1b165a8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	AdeelShahzad	all-rounder	25	2025-11-05 20:28:22.452729	f	\N	{"matches": 3, "runs": 242, "batting_avg": 15.13, "strike_rate": 0.0, "wickets": 18, "bowling_avg": 32.89, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_037	2025-11-05 20:28:22.452891	2025-11-06 09:28:58.73545	\N	0.96	2025-11-05 21:31:58.187649	f
6c55fc42-5141-4c64-8812-ec7413ef41f2	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	AvinashRamkumar	bowler	25	2025-11-05 20:28:22.610183	f	\N	{"matches": 1, "runs": 27, "batting_avg": 5.4, "strike_rate": 0.0, "wickets": 14, "bowling_avg": 24.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_679	2025-11-05 20:28:22.610331	2025-11-06 09:28:58.735451	\N	1.81	2025-11-05 21:31:58.18765	f
6cdc9cf3-96e6-4824-bb38-461db366ec82	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	BramBuytendijk	bowler	25	2025-11-05 20:28:22.749019	f	\N	{"matches": 1, "runs": 25, "batting_avg": 4.17, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 30.17, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_241	2025-11-05 20:28:22.749163	2025-11-06 09:28:58.735451	\N	3.68	2025-11-05 21:31:58.187652	f
6e9a7550-6951-461e-ae7c-cff8cdd8ddb8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	MuzamalIqbal	all-rounder	25	2025-11-05 20:28:22.408412	f	\N	{"matches": 2, "runs": 309, "batting_avg": 18.18, "strike_rate": 0.0, "wickets": 21, "bowling_avg": 24.9, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_135	2025-11-05 20:28:22.408563	2025-11-06 09:28:58.735451	\N	0.94	2025-11-05 21:31:58.187658	f
6f145921-b11e-49a3-9154-2050208a689b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	AlanYadava	batsman	25	2025-11-05 20:28:22.57932	f	\N	{"matches": 4, "runs": 261, "batting_avg": 11.86, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 33.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_129	2025-11-05 20:28:22.579467	2025-11-06 09:28:58.735451	\N	0.99	2025-11-05 21:31:58.187664	f
6f2d890c-d68b-4242-ae74-91674477e360	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	AdeelRaja	all-rounder	25	2025-11-05 20:28:22.540537	f	\N	{"matches": 3, "runs": 225, "batting_avg": 45.0, "strike_rate": 0.0, "wickets": 10, "bowling_avg": 23.4, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_046	2025-11-05 20:28:22.540727	2025-11-06 09:28:58.735451	\N	0.99	2025-11-05 21:31:58.18767	f
6f4b1980-c138-489b-8735-8e5f2bd6aad0	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	DjawidAbqari	all-rounder	25	2025-11-05 20:28:22.541702	f	\N	{"matches": 1, "runs": 179, "batting_avg": 25.57, "strike_rate": 0.0, "wickets": 12, "bowling_avg": 24.33, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_426	2025-11-05 20:28:22.541906	2025-11-06 09:28:58.735452	\N	0.99	2025-11-05 21:31:58.187672	f
6ffd6bd2-673c-48de-b366-7769ee73ff56	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	JoelTharakan	bowler	25	2025-11-05 20:28:22.804485	f	\N	{"matches": 1, "runs": 23, "batting_avg": 7.67, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 40.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_544	2025-11-05 20:28:22.804638	2025-11-06 09:28:58.735452	\N	4.32	2025-11-05 21:31:58.187673	f
700c3aae-56f1-40b0-ae5d-e8239dff6997	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	RohanAngoelal	batsman	25	2025-11-05 20:28:22.788791	f	\N	{"matches": 1, "runs": 60, "batting_avg": 10.0, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 73.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_498	2025-11-05 20:28:22.788967	2025-11-06 09:28:58.735452	\N	4.11	2025-11-05 21:31:58.187675	f
702a639b-f4df-44a8-8126-1f0df8e609b7	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	IrtezaAnwar	all-rounder	25	2025-11-05 20:28:22.339598	f	\N	{"matches": 2, "runs": 707, "batting_avg": 70.7, "strike_rate": 0.0, "wickets": 22, "bowling_avg": 19.91, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_068	2025-11-05 20:28:22.339776	2025-11-06 09:28:58.735452	\N	0.86	2025-11-05 21:31:58.187676	f
70452429-73df-4aaf-b89b-0e2f2f27a4bc	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	HarpreetSingh	batsman	25	2025-11-05 20:28:22.502489	f	\N	{"matches": 1, "runs": 493, "batting_avg": 25.95, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_203	2025-11-05 20:28:22.502632	2025-11-06 09:28:58.735452	\N	0.96	2025-11-05 21:31:58.187678	f
719f40ed-c22a-4b7f-b9a1-01f106a71251	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	JovandeepSingh	batsman	25	2025-11-05 20:28:22.642422	f	\N	{"matches": 9, "runs": 189, "batting_avg": 14.54, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 36.4, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_033	2025-11-05 20:28:22.642619	2025-11-06 09:28:58.735453	\N	1.81	2025-11-05 21:31:58.187681	f
720a669a-4897-486d-9da3-4885cc5a10aa	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	AarushBharali	bowler	25	2025-11-05 20:28:22.796358	f	\N	{"matches": 1, "runs": 9, "batting_avg": 4.5, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 30.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_294	2025-11-05 20:28:22.796515	2025-11-06 09:28:58.735453	\N	4.29	2025-11-05 21:31:58.187682	f
73123f8f-07a5-4b3d-b9bc-6b173b242889	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	HarisMahmood	all-rounder	25	2025-11-05 20:28:22.623451	f	\N	{"matches": 1, "runs": 36, "batting_avg": 5.14, "strike_rate": 0.0, "wickets": 13, "bowling_avg": 21.92, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_589	2025-11-05 20:28:22.62359	2025-11-06 09:28:58.735453	\N	1.96	2025-11-05 21:31:58.187684	f
025c2139-1f9b-4736-bd54-e6d3dc16f20f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	VarunKumar	batsman	25	2025-11-05 20:28:22.706109	f	\N	{"matches": 1, "runs": 159, "batting_avg": 22.71, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 27.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_710	2025-11-05 20:28:22.706268	2025-11-06 09:28:58.735396	\N	2.79	2025-11-05 21:31:58.187042	f
73252dbc-3c46-4b48-b6c1-9e874f04a865	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	RuwanKalupahanage	all-rounder	25	2025-11-05 20:28:22.359375	f	\N	{"matches": 2, "runs": 631, "batting_avg": 31.55, "strike_rate": 0.0, "wickets": 17, "bowling_avg": 27.53, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_045	2025-11-05 20:28:22.359541	2025-11-06 09:28:58.735453	\N	0.89	2025-11-05 21:31:58.187688	f
7382a4cf-1eb7-4458-a7fd-85eb6147c780	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	AnasAmin	all-rounder	25	2025-11-05 20:28:22.524052	f	\N	{"matches": 1, "runs": 180, "batting_avg": 15.0, "strike_rate": 0.0, "wickets": 14, "bowling_avg": 24.86, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_605	2025-11-05 20:28:22.52421	2025-11-06 09:28:58.735453	\N	0.98	2025-11-05 21:31:58.18769	f
73ee0023-454f-4360-b626-62bc24dafe34	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	SamyakJain	bowler	25	2025-11-05 20:28:22.738166	f	\N	{"matches": 2, "runs": 45, "batting_avg": 9.0, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 17.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_512	2025-11-05 20:28:22.738314	2025-11-06 09:28:58.735453	\N	3.49	2025-11-05 21:31:58.187694	f
74b72eb6-780c-474e-ab76-9848e036dfcf	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	ShahidMehmood	batsman	25	2025-11-05 20:28:22.632857	f	\N	{"matches": 1, "runs": 283, "batting_avg": 18.87, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_357	2025-11-05 20:28:22.633027	2025-11-06 09:28:58.735454	\N	1.32	2025-11-05 21:31:58.187698	f
75256ddb-be5b-4028-ad25-4bd67ea686b0	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	MaheshHans	all-rounder	25	2025-11-05 20:28:22.421983	f	\N	{"matches": 1, "runs": 331, "batting_avg": 25.46, "strike_rate": 0.0, "wickets": 17, "bowling_avg": 26.59, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_615	2025-11-05 20:28:22.422135	2025-11-06 09:28:58.735454	\N	0.95	2025-11-05 21:31:58.1877	f
75d5b8eb-af70-4d12-9988-6735bb252ace	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	AmeyaPethe	batsman	25	2025-11-05 20:28:22.620968	f	\N	{"matches": 1, "runs": 286, "batting_avg": 20.43, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 64.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_325	2025-11-05 20:28:22.62111	2025-11-06 09:28:58.735454	\N	1.12	2025-11-05 21:31:58.187707	f
77f58c5c-8461-4476-81b0-538d4178c6ae	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	HeshanWijesinghe	bowler	25	2025-11-05 20:28:22.661746	f	\N	{"matches": 1, "runs": 29, "batting_avg": 9.67, "strike_rate": 0.0, "wickets": 10, "bowling_avg": 12.4, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_627	2025-11-05 20:28:22.661896	2025-11-06 09:28:58.735454	\N	2.71	2025-11-05 21:31:58.187713	f
7852d4c0-9b02-42ce-88b8-86fddfdc1787	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	WimPielage	batsman	25	2025-11-05 20:28:22.563045	f	\N	{"matches": 6, "runs": 175, "batting_avg": 29.17, "strike_rate": 0.0, "wickets": 11, "bowling_avg": 26.73, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_211	2025-11-05 20:28:22.563191	2025-11-06 09:28:58.735455	\N	0.99	2025-11-05 21:31:58.187715	f
78a55733-4254-4fea-a0c3-106919609fb9	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	ManoharanMurugesan	all-rounder	25	2025-11-05 20:28:22.509786	f	\N	{"matches": 1, "runs": 429, "batting_avg": 25.24, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 26.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_332	2025-11-05 20:28:22.509949	2025-11-06 09:28:58.735455	\N	0.97	2025-11-05 21:31:58.187716	f
7b44ed37-04c0-44b5-ad45-a7198f6f49fc	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	LakshayAggarwal	all-rounder	25	2025-11-05 20:28:22.33641	f	\N	{"matches": 2, "runs": 477, "batting_avg": 19.88, "strike_rate": 0.0, "wickets": 36, "bowling_avg": 18.61, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_080	2025-11-05 20:28:22.336576	2025-11-06 09:28:58.735455	\N	0.86	2025-11-05 21:31:58.187719	f
7bd6dec6-72fa-46b8-8770-9d2443057af3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	SunnyGharat	batsman	25	2025-11-05 20:28:22.650151	f	\N	{"matches": 1, "runs": 261, "batting_avg": 21.75, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_424	2025-11-05 20:28:22.650291	2025-11-06 09:28:58.735455	\N	1.64	2025-11-05 21:31:58.187723	f
7c524c64-3d16-4f7e-a843-6303d2cb2211	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	FrankSnieder	all-rounder	25	2025-11-05 20:28:22.537658	f	\N	{"matches": 1, "runs": 78, "batting_avg": 15.6, "strike_rate": 0.0, "wickets": 17, "bowling_avg": 15.35, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_624	2025-11-05 20:28:22.537806	2025-11-06 09:28:58.735456	\N	0.99	2025-11-05 21:31:58.187728	f
7c619bd1-a6ef-4596-812f-c49f81037b42	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	MohyeeAshraf	all-rounder	25	2025-11-05 20:28:22.571841	f	\N	{"matches": 1, "runs": 293, "batting_avg": 19.53, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 31.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_675	2025-11-05 20:28:22.572001	2025-11-06 09:28:58.735456	\N	0.99	2025-11-05 21:31:58.18773	f
7c8886a4-488c-4ea1-ac8e-e82d7907ca9c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	RobertJordaan	all-rounder	25	2025-11-05 20:28:22.340714	f	\N	{"matches": 2, "runs": 640, "batting_avg": 58.18, "strike_rate": 0.0, "wickets": 25, "bowling_avg": 20.68, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_293	2025-11-05 20:28:22.340912	2025-11-06 09:28:58.735456	\N	0.86	2025-11-05 21:31:58.187731	f
7d24d7e2-845b-498f-a998-67ff746d985d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	AdeelHaq	all-rounder	25	2025-11-05 20:28:22.503433	f	\N	{"matches": 1, "runs": 346, "batting_avg": 26.62, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 41.63, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_616	2025-11-05 20:28:22.503576	2025-11-06 09:28:58.735456	\N	0.97	2025-11-05 21:31:58.187734	f
7dbd4577-1a1e-4ac5-89ba-9a4df4b9dac9	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	ArsalanAlim	batsman	25	2025-11-05 20:28:22.507011	f	\N	{"matches": 8, "runs": 486, "batting_avg": 40.5, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_108	2025-11-05 20:28:22.507167	2025-11-06 09:28:58.735456	\N	0.96	2025-11-05 21:31:58.187736	f
769b97ef-04ea-493d-8be8-7845e6aab136	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	BaljotSingh	batsman	25	2025-11-05 20:28:22.331932	f	\N	{"matches": 11, "runs": 740, "batting_avg": 56.92, "strike_rate": 0.0, "wickets": 28, "bowling_avg": 17.14, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_004	2025-11-05 20:28:22.332143	2025-11-06 10:09:45.311675	\N	0.83	2025-11-05 21:31:58.187711	t
7f273c91-1e7c-49c5-a6a9-da6eda24c9ec	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	RouhinBanerjee	bowler	25	2025-11-05 20:28:22.768392	f	\N	{"matches": 6, "runs": 15, "batting_avg": 2.5, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 29.8, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_224	2025-11-05 20:28:22.768549	2025-11-06 09:28:58.735456	\N	4	2025-11-05 21:31:58.187738	f
7f278ae2-b4ed-40b8-86fc-d59ad476efe5	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	AmrenderGhangas	all-rounder	25	2025-11-05 20:28:22.615739	f	\N	{"matches": 2, "runs": 80, "batting_avg": 6.67, "strike_rate": 0.0, "wickets": 12, "bowling_avg": 23.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_553	2025-11-05 20:28:22.615905	2025-11-06 09:28:58.735457	\N	1.71	2025-11-05 21:31:58.18774	f
7f701d77-50ee-4076-9ff0-b88cb72aef37	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	AdvayChandra	all-rounder	25	2025-11-05 20:28:22.709535	f	\N	{"matches": 1, "runs": 54, "batting_avg": 9.0, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 30.43, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_425	2025-11-05 20:28:22.709678	2025-11-06 09:28:58.735457	\N	3.16	2025-11-05 21:31:58.187741	f
8109c37b-da04-4339-a0c2-4653c04a735d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	UmairTariq	all-rounder	25	2025-11-05 20:28:22.486189	f	\N	{"matches": 1, "runs": 403, "batting_avg": 23.71, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 25.86, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_207	2025-11-05 20:28:22.486359	2025-11-06 09:28:58.735457	\N	0.96	2025-11-05 21:31:58.187748	f
81a2d3dc-03b8-4335-b999-b3a7a4125248	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	VivaanDhawan	all-rounder	25	2025-11-05 20:28:22.335355	f	\N	{"matches": 1, "runs": 470, "batting_avg": 22.38, "strike_rate": 0.0, "wickets": 37, "bowling_avg": 20.49, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_213	2025-11-05 20:28:22.335525	2025-11-06 09:28:58.735457	\N	0.86	2025-11-05 21:31:58.187751	f
81df0839-1701-4af1-b588-6342b92c5377	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	AhmadullahKakar	all-rounder	25	2025-11-05 20:28:22.641194	f	\N	{"matches": 1, "runs": 211, "batting_avg": 21.1, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 56.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_419	2025-11-05 20:28:22.641453	2025-11-06 09:28:58.735457	\N	1.72	2025-11-05 21:31:58.187755	f
81e6ed67-3261-483a-8a93-a61a49af87b9	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	DoreeKouwenhoven	bowler	25	2025-11-05 20:28:22.837051	f	\N	{"matches": 2, "runs": 6, "batting_avg": 3.0, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 37.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_621	2025-11-05 20:28:22.837228	2025-11-06 09:28:58.735458	\N	4.64	2025-11-05 21:31:58.187756	f
829ed784-010e-4249-ad6a-452da85367b8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	RohitKapote	batsman	25	2025-11-05 20:28:22.703296	f	\N	{"matches": 1, "runs": 160, "batting_avg": 16.0, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 60.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_500	2025-11-05 20:28:22.703442	2025-11-06 09:28:58.735458	\N	2.78	2025-11-05 21:31:58.187759	f
83418825-ada3-469b-976b-2eb320fbe0e3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	HashanKulasinghe	all-rounder	25	2025-11-05 20:28:22.614984	f	\N	{"matches": 1, "runs": 190, "batting_avg": 15.83, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 15.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_093	2025-11-05 20:28:22.615133	2025-11-06 09:28:58.735458	\N	1.33	2025-11-05 21:31:58.18776	f
835c9513-385c-432a-89fd-36237ec0c0f5	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	JamalGhairat	all-rounder	25	2025-11-05 20:28:22.410203	f	\N	{"matches": 2, "runs": 572, "batting_avg": 35.75, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 60.25, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_505	2025-11-05 20:28:22.410347	2025-11-06 09:28:58.735458	\N	0.93	2025-11-05 21:31:58.187762	f
84267f45-af5c-4c42-a820-039865e6456f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	MushafMian	all-rounder	25	2025-11-05 20:28:22.663623	f	\N	{"matches": 1, "runs": 102, "batting_avg": 34.0, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 29.71, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_420	2025-11-05 20:28:22.663772	2025-11-06 09:28:58.735458	\N	2.6	2025-11-05 21:31:58.187765	f
846a8ea8-d9d9-4865-8e6a-0bf3a7c64f78	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	MohsinKhan	all-rounder	25	2025-11-05 20:28:22.577434	f	\N	{"matches": 1, "runs": 64, "batting_avg": 7.11, "strike_rate": 0.0, "wickets": 15, "bowling_avg": 19.73, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_174	2025-11-05 20:28:22.577581	2025-11-06 09:28:58.735458	\N	1.2	2025-11-05 21:31:58.187769	f
84745bb2-dc74-4929-85da-a2353b8b6e82	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	RobertKottman	all-rounder	25	2025-11-05 20:28:22.646035	f	\N	{"matches": 1, "runs": 144, "batting_avg": 28.8, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 18.57, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_591	2025-11-05 20:28:22.646198	2025-11-06 09:28:58.735459	\N	2	2025-11-05 21:31:58.18777	f
8480bbc6-623d-400e-b4d6-6e0665391870	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	KaranPawa	all-rounder	25	2025-11-05 20:28:22.618016	f	\N	{"matches": 2, "runs": 163, "batting_avg": 20.38, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 32.63, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_554	2025-11-05 20:28:22.618167	2025-11-06 09:28:58.735459	\N	1.49	2025-11-05 21:31:58.187772	f
84b0e948-1c9d-47a3-9629-0f97cced849c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	ZalandZazai	all-rounder	25	2025-11-05 20:28:22.791154	f	\N	{"matches": 1, "runs": 39, "batting_avg": 13.0, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 45.67, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_471	2025-11-05 20:28:22.791322	2025-11-06 09:28:58.735459	\N	4.17	2025-11-05 21:31:58.187773	f
85b0786d-8c22-4ac3-bf30-99a04e3039e6	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	VivaanJethva	batsman	25	2025-11-05 20:28:22.680444	f	\N	{"matches": 6, "runs": 104, "batting_avg": 20.8, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 28.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_305	2025-11-05 20:28:22.680597	2025-11-06 09:28:58.735459	\N	2.81	2025-11-05 21:31:58.187778	f
85fc584c-f2a6-470d-8e4b-bdcd013f4ddd	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	JustinCampbell	bowler	25	2025-11-05 20:28:22.697167	f	\N	{"matches": 1, "runs": 10, "batting_avg": 3.33, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 21.56, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_724	2025-11-05 20:28:22.697317	2025-11-06 09:28:58.735459	\N	3.12	2025-11-05 21:31:58.18778	f
86a2b042-fc2b-4960-a1ac-eec4554c5fb6	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	ModassirSiddiqui	all-rounder	25	2025-11-05 20:28:22.352203	f	\N	{"matches": 1, "runs": 629, "batting_avg": 44.93, "strike_rate": 0.0, "wickets": 19, "bowling_avg": 29.32, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_691	2025-11-05 20:28:22.352356	2025-11-06 09:28:58.73546	\N	0.88	2025-11-05 21:31:58.187781	f
87077270-44b0-416d-97d3-dac0ea7ff6bb	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	AliSaeed	all-rounder	25	2025-11-05 20:28:22.34541	f	\N	{"matches": 2, "runs": 649, "batting_avg": 28.22, "strike_rate": 0.0, "wickets": 22, "bowling_avg": 25.64, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_226	2025-11-05 20:28:22.345572	2025-11-06 09:28:58.73546	\N	0.87	2025-11-05 21:31:58.187783	f
871bd2c1-1c02-418e-bdd4-7f2edf19f9bd	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	AryanWarrier	bowler	25	2025-11-05 20:28:22.846553	f	\N	{"matches": 1, "runs": 6, "batting_avg": 3.0, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 88.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_527	2025-11-05 20:28:22.846733	2025-11-06 09:28:58.73546	\N	4.79	2025-11-05 21:31:58.187789	f
880a76e3-5423-4ca3-a754-d1263af3df76	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	DaiwikDaksh	all-rounder	25	2025-11-05 20:28:22.570082	f	\N	{"matches": 2, "runs": 230, "batting_avg": 17.69, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 30.63, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_310	2025-11-05 20:28:22.570228	2025-11-06 09:28:58.73546	\N	0.99	2025-11-05 21:31:58.187793	f
89d967e0-9c53-47fc-bab4-5c6b20aecce2	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	AdhrutaNaropanth	batsman	25	2025-11-05 20:28:22.862619	f	\N	{"matches": 1, "runs": 3, "batting_avg": 0.75, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_720	2025-11-05 20:28:22.862779	2025-11-06 09:28:58.73546	\N	4.98	2025-11-05 21:31:58.187795	f
8ae0aed9-3905-46db-9a33-ce33d86416b0	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	DhilanBisessar	bowler	25	2025-11-05 20:28:22.851999	f	\N	{"matches": 1, "runs": 1, "batting_avg": 1.0, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 165.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_701	2025-11-05 20:28:22.85216	2025-11-06 09:28:58.735461	\N	4.84	2025-11-05 21:31:58.187799	f
8b011044-6f70-4d49-8e8e-b19d40db1303	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	MohammedNaqvi	batsman	25	2025-11-05 20:28:22.468621	f	\N	{"matches": 1, "runs": 545, "batting_avg": 28.68, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 12.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_356	2025-11-05 20:28:22.468762	2025-11-06 09:28:58.735461	\N	0.95	2025-11-05 21:31:58.187801	f
8b27a7f2-e91a-43b0-be99-0350b2cce140	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	RajeshYadav	all-rounder	25	2025-11-05 20:28:22.404865	f	\N	{"matches": 1, "runs": 658, "batting_avg": 34.63, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 76.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_559	2025-11-05 20:28:22.405023	2025-11-06 09:28:58.735461	\N	0.92	2025-11-05 21:31:58.187804	f
8b8c2e6b-df1b-4f6b-87f6-f135ad274acb	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	SuryaNaragani	bowler	25	2025-11-05 20:28:22.637359	f	\N	{"matches": 2, "runs": 36, "batting_avg": 9.0, "strike_rate": 0.0, "wickets": 12, "bowling_avg": 31.17, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_075	2025-11-05 20:28:22.637503	2025-11-06 09:28:58.735461	\N	2.19	2025-11-05 21:31:58.187808	f
8c2eee25-71c5-45c7-92c9-86492e2aaa0f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	RiaanSehgal	batsman	25	2025-11-05 20:28:22.628992	f	\N	{"matches": 8, "runs": 144, "batting_avg": 10.29, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 34.63, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_060	2025-11-05 20:28:22.629142	2025-11-06 09:28:58.735461	\N	1.77	2025-11-05 21:31:58.187811	f
8c3cfa94-44cf-48ff-a9bd-b78690bd95c1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	MostafaQuderty	all-rounder	25	2025-11-05 20:28:22.483514	f	\N	{"matches": 1, "runs": 81, "batting_avg": 6.23, "strike_rate": 0.0, "wickets": 22, "bowling_avg": 32.27, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_713	2025-11-05 20:28:22.483682	2025-11-06 09:28:58.735461	\N	0.98	2025-11-05 21:31:58.187813	f
8cb49dc3-baf9-4fe7-9777-2c9acff0ce0a	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	JatinKumar	batsman	25	2025-11-05 20:28:22.819479	f	\N	{"matches": 1, "runs": 21, "batting_avg": 7.0, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 6.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_326	2025-11-05 20:28:22.819723	2025-11-06 09:28:58.735462	\N	4.49	2025-11-05 21:31:58.187814	f
8cd84df7-ac4c-41a3-b6bf-3bdcb69d3eff	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	RichardWolfe	batsman	25	2025-11-05 20:28:22.616518	f	\N	{"matches": 7, "runs": 249, "batting_avg": 35.57, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 34.25, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_131	2025-11-05 20:28:22.616661	2025-11-06 09:28:58.735462	\N	1.17	2025-11-05 21:31:58.187816	f
8cea4a0a-ae7a-4b63-8138-b9c9becdbfa9	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	IhsanMohammad	bowler	25	2025-11-05 20:28:22.700067	f	\N	{"matches": 1, "runs": 3, "batting_avg": 0.43, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 36.56, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_723	2025-11-05 20:28:22.700238	2025-11-06 09:28:58.735462	\N	3.19	2025-11-05 21:31:58.187818	f
8cffcae9-6927-4351-919c-61ebe4f48c6e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	EvertBrouwer	bowler	25	2025-11-05 20:28:22.651694	f	\N	{"matches": 1, "runs": 25, "batting_avg": 8.33, "strike_rate": 0.0, "wickets": 11, "bowling_avg": 25.36, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_631	2025-11-05 20:28:22.651834	2025-11-06 09:28:58.735462	\N	2.52	2025-11-05 21:31:58.187819	f
8dc76dd7-9cf4-4054-b230-89e1a162b6d7	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	SaneelMahulkar	all-rounder	25	2025-11-05 20:28:22.635713	f	\N	{"matches": 2, "runs": 94, "batting_avg": 13.43, "strike_rate": 0.0, "wickets": 10, "bowling_avg": 32.8, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_062	2025-11-05 20:28:22.63586	2025-11-06 09:28:58.735462	\N	2.01	2025-11-05 21:31:58.187821	f
8ddf3247-e79f-42a0-9ed9-fcd225e8e17c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	AbhisaarBhatnagar	all-rounder	25	2025-11-05 20:28:22.625014	f	\N	{"matches": 2, "runs": 63, "batting_avg": 10.5, "strike_rate": 0.0, "wickets": 12, "bowling_avg": 34.58, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_300	2025-11-05 20:28:22.625154	2025-11-06 09:28:58.735463	\N	1.9	2025-11-05 21:31:58.187825	f
8e02b6ae-3692-42e7-a63f-4a08551fa9ef	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	MartijnBesier	all-rounder	25	2025-11-05 20:28:22.38425	f	\N	{"matches": 1, "runs": 149, "batting_avg": 14.9, "strike_rate": 0.0, "wickets": 34, "bowling_avg": 17.85, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_257	2025-11-05 20:28:22.384396	2025-11-06 09:28:58.735463	\N	0.93	2025-11-05 21:31:58.187826	f
8e05d4e1-18d0-4272-b0af-d23de8c19449	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	ShatrudamanSharma	batsman	25	2025-11-05 20:28:22.557644	f	\N	{"matches": 1, "runs": 358, "batting_avg": 39.78, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 8.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_340	2025-11-05 20:28:22.557789	2025-11-06 09:28:58.735463	\N	0.99	2025-11-05 21:31:58.187828	f
8ee902d2-ec8a-4e60-8c98-e342c2d80db7	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	SohailKakar	batsman	25	2025-11-05 20:28:22.742258	f	\N	{"matches": 1, "runs": 156, "batting_avg": 26.0, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_695	2025-11-05 20:28:22.742415	2025-11-06 09:28:58.735463	\N	3.15	2025-11-05 21:31:58.187829	f
907d8c76-7033-4141-9f49-53ef6a6df0bc	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	AaravPatel	batsman	25	2025-11-05 20:28:22.752694	f	\N	{"matches": 1, "runs": 110, "batting_avg": 22.0, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 38.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_284	2025-11-05 20:28:22.752838	2025-11-06 09:28:58.735463	\N	3.5	2025-11-05 21:31:58.187833	f
915009dc-e34e-45f9-b64a-e40136f330e1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	AdilAwan	bowler	25	2025-11-05 20:28:22.638887	f	\N	{"matches": 1, "runs": 0, "batting_avg": 0.0, "strike_rate": 0.0, "wickets": 13, "bowling_avg": 22.08, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_531	2025-11-05 20:28:22.63903	2025-11-06 09:28:58.735464	\N	2.29	2025-11-05 21:31:58.187834	f
919256c1-4987-4216-9fa8-b100875cefde	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	ImranChoudry	all-rounder	25	2025-11-05 20:28:22.42496	f	\N	{"matches": 2, "runs": 364, "batting_avg": 26.0, "strike_rate": 0.0, "wickets": 15, "bowling_avg": 37.33, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_429	2025-11-05 20:28:22.425129	2025-11-06 09:28:58.735464	\N	0.95	2025-11-05 21:31:58.187836	f
9245c119-3196-42f6-b8f6-db49c8b2c0c4	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	AbhinavVelidandla	batsman	25	2025-11-05 20:28:22.717031	f	\N	{"matches": 7, "runs": 118, "batting_avg": 16.86, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 39.25, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_158	2025-11-05 20:28:22.717183	2025-11-06 09:28:58.735464	\N	3.07	2025-11-05 21:31:58.187843	f
924b4ed9-f850-46bc-8db6-c4b27a6c3bd3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	KaramjitSingh	all-rounder	25	2025-11-05 20:28:22.534825	f	\N	{"matches": 1, "runs": 169, "batting_avg": 9.94, "strike_rate": 0.0, "wickets": 13, "bowling_avg": 26.92, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_705	2025-11-05 20:28:22.535029	2025-11-06 09:28:58.735469	\N	0.99	2025-11-05 21:31:58.187847	f
92ba3872-821d-46b8-ad78-e26fc59c2a85	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	AnjanaNarayanamoorthy	batsman	25	2025-11-05 20:28:22.779393	f	\N	{"matches": 1, "runs": 89, "batting_avg": 5.93, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 63.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_732	2025-11-05 20:28:22.779555	2025-11-06 09:28:58.735469	\N	3.93	2025-11-05 21:31:58.18785	f
92d8948d-d805-4c13-98d8-d561231fcc1a	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	RubenVissers	batsman	25	2025-11-05 20:28:22.66271	f	\N	{"matches": 1, "runs": 230, "batting_avg": 46.0, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_530	2025-11-05 20:28:22.662889	2025-11-06 09:28:58.735469	\N	2.08	2025-11-05 21:31:58.187852	f
93f914dc-dca0-4e3b-8248-62043607d234	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	EDemichelis	bowler	25	2025-11-05 20:28:22.811225	f	\N	{"matches": 4, "runs": 8, "batting_avg": 2.67, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 35.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_319	2025-11-05 20:28:22.811397	2025-11-06 09:28:58.73547	\N	4.46	2025-11-05 21:31:58.187853	f
947d8bae-e625-4d0a-8659-e0db8a4aa93b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	AjaySaggar	batsman	25	2025-11-05 20:28:22.777305	f	\N	{"matches": 1, "runs": 90, "batting_avg": 18.0, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 78.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_415	2025-11-05 20:28:22.777463	2025-11-06 09:28:58.73547	\N	3.92	2025-11-05 21:31:58.18786	f
94a71488-a08c-46a5-8ff0-07e2c7b65123	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	SaqibullahUsmanzai	all-rounder	25	2025-11-05 20:28:22.455434	f	\N	{"matches": 1, "runs": 304, "batting_avg": 15.2, "strike_rate": 0.0, "wickets": 15, "bowling_avg": 30.93, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_088	2025-11-05 20:28:22.455583	2025-11-06 09:28:58.73547	\N	0.96	2025-11-05 21:31:58.187862	f
9584a9cb-81e1-48eb-9165-8ddde91e4484	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	HamidullahShinwari	all-rounder	25	2025-11-05 20:28:22.634822	f	\N	{"matches": 1, "runs": 238, "batting_avg": 23.8, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 15.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_711	2025-11-05 20:28:22.634982	2025-11-06 09:28:58.735471	\N	1.49	2025-11-05 21:31:58.187865	f
95c6375c-3720-4db8-96e8-a941a807ffaf	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	KishankumarPatel	batsman	25	2025-11-05 20:28:22.515466	f	\N	{"matches": 2, "runs": 387, "batting_avg": 29.77, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 56.4, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_367	2025-11-05 20:28:22.515616	2025-11-06 09:28:58.735471	\N	0.97	2025-11-05 21:31:58.18787	f
974816e4-544b-4d6e-8804-13575b637da2	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	BrandonMadgwick	all-rounder	25	2025-11-05 20:28:22.654529	f	\N	{"matches": 1, "runs": 46, "batting_avg": 7.67, "strike_rate": 0.0, "wickets": 10, "bowling_avg": 12.4, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_671	2025-11-05 20:28:22.654697	2025-11-06 09:28:58.735471	\N	2.55	2025-11-05 21:31:58.187875	f
97cd14e3-c10a-4290-926a-fc2f536eba90	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	PrakashAzhagappan	all-rounder	25	2025-11-05 20:28:22.484616	f	\N	{"matches": 2, "runs": 126, "batting_avg": 15.75, "strike_rate": 0.0, "wickets": 20, "bowling_avg": 19.65, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_490	2025-11-05 20:28:22.484793	2025-11-06 09:28:58.735471	\N	0.98	2025-11-05 21:31:58.187882	f
99eb8d72-f4c4-4d69-afa6-d11263281489	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	VarunGoel	batsman	25	2025-11-05 20:28:22.656493	f	\N	{"matches": 4, "runs": 241, "batting_avg": 15.06, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_077	2025-11-05 20:28:22.656645	2025-11-06 09:28:58.735472	\N	1.92	2025-11-05 21:31:58.187887	f
9a60a4f2-4d70-4429-b361-e1aaeed732b9	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	PatrickReardon	all-rounder	25	2025-11-05 20:28:22.528643	f	\N	{"matches": 1, "runs": 43, "batting_avg": 14.33, "strike_rate": 0.0, "wickets": 19, "bowling_avg": 12.68, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_620	2025-11-05 20:28:22.52879	2025-11-06 09:28:58.735472	\N	0.99	2025-11-05 21:31:58.187889	f
9ab0362a-b6c9-4250-bf88-2e050f67648d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	AkaashMahangoe	bowler	25	2025-11-05 20:28:22.727014	f	\N	{"matches": 2, "runs": 30, "batting_avg": 5.0, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 28.57, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_349	2025-11-05 20:28:22.727172	2025-11-06 09:28:58.735472	\N	3.4	2025-11-05 21:31:58.18789	f
9b9b3697-9bd3-4204-a26f-51abeb1ef979	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	DhananjayKhamankar	all-rounder	25	2025-11-05 20:28:22.382437	f	\N	{"matches": 2, "runs": 365, "batting_avg": 22.81, "strike_rate": 0.0, "wickets": 24, "bowling_avg": 33.04, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_029	2025-11-05 20:28:22.382591	2025-11-06 09:28:58.735472	\N	0.92	2025-11-05 21:31:58.187894	f
9ba67ce8-624e-4aeb-86a7-eaf9742f618d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	MartinKrop	batsman	25	2025-11-05 20:28:22.706927	f	\N	{"matches": 1, "runs": 173, "batting_avg": 14.42, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 53.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_212	2025-11-05 20:28:22.707077	2025-11-06 09:28:58.735472	\N	2.75	2025-11-05 21:31:58.187903	f
9c012e99-bde6-4e7c-8b2e-40411c6c6c24	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	QuirijnGunning	all-rounder	25	2025-11-05 20:28:22.413115	f	\N	{"matches": 1, "runs": 156, "batting_avg": 15.6, "strike_rate": 0.0, "wickets": 27, "bowling_avg": 16.59, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_676	2025-11-05 20:28:22.413273	2025-11-06 09:28:58.735473	\N	0.95	2025-11-05 21:31:58.187905	f
9c1a5c81-1137-4ec4-b232-a9c2cddeb82e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	LalitGurnani	bowler	25	2025-11-05 20:28:22.469493	f	\N	{"matches": 7, "runs": 28, "batting_avg": 7.0, "strike_rate": 0.0, "wickets": 25, "bowling_avg": 24.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_134	2025-11-05 20:28:22.469635	2025-11-06 09:28:58.735473	\N	0.98	2025-11-05 21:31:58.187907	f
9c271ad7-1213-4a09-ab80-4bb0741a7cff	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	NewtonPawlish	all-rounder	25	2025-11-05 20:28:22.533463	f	\N	{"matches": 1, "runs": 128, "batting_avg": 11.64, "strike_rate": 0.0, "wickets": 15, "bowling_avg": 25.07, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_634	2025-11-05 20:28:22.533644	2025-11-06 09:28:58.735473	\N	0.99	2025-11-05 21:31:58.187908	f
9cb710e5-9677-4f82-8d20-e6992e7aa1cd	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	AniruddhaSengupta	all-rounder	25	2025-11-05 20:28:22.514256	f	\N	{"matches": 1, "runs": 424, "batting_avg": 30.29, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 27.67, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_703	2025-11-05 20:28:22.514401	2025-11-06 09:28:58.735473	\N	0.97	2025-11-05 21:31:58.187912	f
9d7d0ff6-3af5-4482-a5b4-a9d0e1ba18b9	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	AryanBellad	batsman	25	2025-11-05 20:28:22.763772	f	\N	{"matches": 1, "runs": 107, "batting_avg": 35.67, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 171.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_596	2025-11-05 20:28:22.763932	2025-11-06 09:28:58.735474	\N	3.7	2025-11-05 21:31:58.187915	f
9d9e3c4f-ea3f-4350-89d4-ff2c912c00f7	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	WahiduleMasood	all-rounder	25	2025-11-05 20:28:22.393843	f	\N	{"matches": 2, "runs": 208, "batting_avg": 17.33, "strike_rate": 0.0, "wickets": 29, "bowling_avg": 18.03, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_216	2025-11-05 20:28:22.394006	2025-11-06 09:28:58.735474	\N	0.93	2025-11-05 21:31:58.187917	f
9e2ecbcd-8356-49a9-a6be-dd52a92d31ec	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	VictorLubbers	all-rounder	25	2025-11-05 20:28:22.498884	f	\N	{"matches": 1, "runs": 252, "batting_avg": 28.0, "strike_rate": 0.0, "wickets": 13, "bowling_avg": 20.46, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_035	2025-11-05 20:28:22.499042	2025-11-06 09:28:58.735474	\N	0.97	2025-11-05 21:31:58.187918	f
9e9e4d96-d3f1-4eb8-9d67-7bad1797c23b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	OlePototsky	all-rounder	25	2025-11-05 20:28:22.678325	f	\N	{"matches": 1, "runs": 148, "batting_avg": 18.5, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 45.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_139	2025-11-05 20:28:22.678474	2025-11-06 09:28:58.735474	\N	2.63	2025-11-05 21:31:58.187924	f
9f6f64c8-e751-4686-b707-79a3de809966	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	KodiVishal	all-rounder	25	2025-11-05 20:28:22.428171	f	\N	{"matches": 1, "runs": 333, "batting_avg": 27.75, "strike_rate": 0.0, "wickets": 16, "bowling_avg": 29.88, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_458	2025-11-05 20:28:22.428339	2025-11-06 09:28:58.735475	\N	0.95	2025-11-05 21:31:58.187928	f
9fd480cc-4434-4fba-a213-e5ecf54eac30	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	MirzaHassan	all-rounder	25	2025-11-05 20:28:22.461911	f	\N	{"matches": 1, "runs": 435, "batting_avg": 31.07, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 35.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_228	2025-11-05 20:28:22.462064	2025-11-06 09:28:58.735475	\N	0.95	2025-11-05 21:31:58.18793	f
a0126b2f-d744-42e3-ad7a-a33ee87472aa	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	BrandenTaeuber	all-rounder	25	2025-11-05 20:28:22.33845	f	\N	{"matches": 1, "runs": 370, "batting_avg": 26.43, "strike_rate": 0.0, "wickets": 38, "bowling_avg": 16.47, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_602	2025-11-05 20:28:22.338616	2025-11-06 09:28:58.735475	\N	0.87	2025-11-05 21:31:58.187931	f
a0d25045-522c-4c5e-917b-b810521b01ec	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	SahirNaqash	batsman	25	2025-11-05 20:28:22.547493	f	\N	{"matches": 1, "runs": 371, "batting_avg": 23.19, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 57.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_059	2025-11-05 20:28:22.547655	2025-11-06 09:28:58.735475	\N	0.98	2025-11-05 21:31:58.187935	f
a10e7473-c6d6-43d3-a6a5-688cbf08c97b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	GauravKwatra	bowler	25	2025-11-05 20:28:22.601153	f	\N	{"matches": 8, "runs": 72, "batting_avg": 14.4, "strike_rate": 0.0, "wickets": 13, "bowling_avg": 26.08, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_156	2025-11-05 20:28:22.601296	2025-11-06 09:28:58.735475	\N	1.57	2025-11-05 21:31:58.187947	f
a130146d-439c-4474-9a42-9fcd937a58aa	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	ShankarIyer	batsman	25	2025-11-05 20:28:22.553088	f	\N	{"matches": 7, "runs": 311, "batting_avg": 25.92, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 22.8, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_278	2025-11-05 20:28:22.553235	2025-11-06 09:28:58.735475	\N	0.99	2025-11-05 21:31:58.187948	f
a13642e3-a680-4225-83ef-d52264f79aef	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	KrishnakanthAjjarapu	bowler	25	2025-11-05 20:28:22.619788	f	\N	{"matches": 1, "runs": 7, "batting_avg": 1.75, "strike_rate": 0.0, "wickets": 14, "bowling_avg": 30.57, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_140	2025-11-05 20:28:22.619949	2025-11-06 09:28:58.735476	\N	2	2025-11-05 21:31:58.18795	f
a14a758b-0753-4101-9cb2-04123def005d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	AnthonyCronje	batsman	25	2025-11-05 20:28:22.770398	f	\N	{"matches": 2, "runs": 82, "batting_avg": 5.13, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 83.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_606	2025-11-05 20:28:22.770556	2025-11-06 09:28:58.735476	\N	3.85	2025-11-05 21:31:58.187952	f
a17d53dd-bc84-40f4-965a-bda3e5d2fac6	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	AkshaySingh	all-rounder	25	2025-11-05 20:28:22.611489	f	\N	{"matches": 1, "runs": 171, "batting_avg": 17.1, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 15.38, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_718	2025-11-05 20:28:22.611633	2025-11-06 09:28:58.735476	\N	1.38	2025-11-05 21:31:58.187953	f
a210fd9b-6f85-4ec2-8de7-595cc39415a1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	PremkumarGanesan	all-rounder	25	2025-11-05 20:28:22.593852	f	\N	{"matches": 1, "runs": 170, "batting_avg": 28.33, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 20.56, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_515	2025-11-05 20:28:22.594012	2025-11-06 09:28:58.735476	\N	1.16	2025-11-05 21:31:58.187958	f
a39d0cb3-90bb-4423-a005-ec71593448df	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	HimanshuSingh	all-rounder	25	2025-11-05 20:28:22.448051	f	\N	{"matches": 1, "runs": 120, "batting_avg": 10.91, "strike_rate": 0.0, "wickets": 24, "bowling_avg": 18.08, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_380	2025-11-05 20:28:22.448202	2025-11-06 09:28:58.735476	\N	0.97	2025-11-05 21:31:58.187965	f
a3e2e08d-8bd1-4776-991a-c213c025d118	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	BartSandberg	batsman	25	2025-11-05 20:28:22.554913	f	\N	{"matches": 5, "runs": 181, "batting_avg": 45.25, "strike_rate": 0.0, "wickets": 11, "bowling_avg": 17.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_320	2025-11-05 20:28:22.555068	2025-11-06 09:28:58.735477	\N	0.99	2025-11-05 21:31:58.187967	f
a4385a7f-331c-4c17-a0c0-c4d2b6b2461e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	ChristopherBraine	batsman	25	2025-11-05 20:28:22.749932	f	\N	{"matches": 1, "runs": 112, "batting_avg": 18.67, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 54.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_448	2025-11-05 20:28:22.750077	2025-11-06 09:28:58.735477	\N	3.47	2025-11-05 21:31:58.187968	f
a46309e5-3877-427e-b395-60cb41c3c3b8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	ZamaanKhan	batsman	25	2025-11-05 20:28:22.628169	f	\N	{"matches": 2, "runs": 259, "batting_avg": 12.33, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 21.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_360	2025-11-05 20:28:22.62831	2025-11-06 09:28:58.735477	\N	1.35	2025-11-05 21:31:58.18797	f
a4b0c8b5-a71b-40f9-91e2-9fe26075dd11	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	NandanPatil	batsman	25	2025-11-05 20:28:22.553976	f	\N	{"matches": 1, "runs": 391, "batting_avg": 23.0, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_492	2025-11-05 20:28:22.554122	2025-11-06 09:28:58.735477	\N	0.98	2025-11-05 21:31:58.187973	f
a4bccef5-cb34-4f84-99e9-cdcefa970f2b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	VishwdeepVaid	all-rounder	25	2025-11-05 20:28:22.353157	f	\N	{"matches": 2, "runs": 362, "batting_avg": 25.86, "strike_rate": 0.0, "wickets": 31, "bowling_avg": 14.32, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_523	2025-11-05 20:28:22.353325	2025-11-06 09:28:58.735477	\N	0.9	2025-11-05 21:31:58.187975	f
a5b4b438-1385-4ffa-a808-d74056e14064	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	PrasunBanerjee	batsman	25	2025-11-05 20:28:22.456325	f	\N	{"matches": 1, "runs": 593, "batting_avg": 24.71, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_315	2025-11-05 20:28:22.456473	2025-11-06 09:28:58.735478	\N	0.94	2025-11-05 21:31:58.187976	f
a626543e-a37a-4607-9cc9-4dd5a11e63f1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	ReinierVos	all-rounder	25	2025-11-05 20:28:22.592063	f	\N	{"matches": 1, "runs": 194, "batting_avg": 32.33, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 26.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_217	2025-11-05 20:28:22.592206	2025-11-06 09:28:58.735478	\N	1.04	2025-11-05 21:31:58.187978	f
a6b90d7e-a1a3-4d56-8a33-d80656b3f3b9	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	BasStembord	batsman	25	2025-11-05 20:28:22.734419	f	\N	{"matches": 1, "runs": 158, "batting_avg": 11.29, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_250	2025-11-05 20:28:22.734563	2025-11-06 09:28:58.735478	\N	3.12	2025-11-05 21:31:58.187982	f
a6ba9df7-3a6d-4e1e-89da-9d0af7b34c69	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	AgrimMahana	all-rounder	25	2025-11-05 20:28:22.600258	f	\N	{"matches": 1, "runs": 184, "batting_avg": 20.44, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 17.25, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_416	2025-11-05 20:28:22.600404	2025-11-06 09:28:58.735478	\N	1.19	2025-11-05 21:31:58.187983	f
a8ab73d1-3b71-4a81-b823-5036878eb922	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	PratheekPerala	all-rounder	25	2025-11-05 20:28:22.588443	f	\N	{"matches": 1, "runs": 116, "batting_avg": 29.0, "strike_rate": 0.0, "wickets": 12, "bowling_avg": 36.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_539	2025-11-05 20:28:22.588585	2025-11-06 09:28:58.735479	\N	1.25	2025-11-05 21:31:58.18799	f
a91b184a-1909-4579-921f-470855feee3e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	RohitManethiya	batsman	25	2025-11-05 20:28:22.491635	f	\N	{"matches": 7, "runs": 497, "batting_avg": 45.18, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 28.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_198	2025-11-05 20:28:22.491802	2025-11-06 09:28:58.735479	\N	0.96	2025-11-05 21:31:58.187996	f
a947f35d-2d7b-4cf5-a504-c593f31b5b88	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	CasimirBoom	batsman	25	2025-11-05 20:28:22.857737	f	\N	{"matches": 1, "runs": 7, "batting_avg": 1.75, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_312	2025-11-05 20:28:22.857949	2025-11-06 09:28:58.735479	\N	4.94	2025-11-05 21:31:58.187998	f
a9dd3458-eb63-4688-8820-394c1339c01e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	ShahzaibMirza	batsman	25	2025-11-05 20:28:22.733475	f	\N	{"matches": 8, "runs": 101, "batting_avg": 11.22, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 31.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_098	2025-11-05 20:28:22.733619	2025-11-06 09:28:58.735479	\N	3.31	2025-11-05 21:31:58.188	f
a9f9b3c8-2da4-4b37-b032-faeb0d336a90	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	AhmerAltaf	batsman	25	2025-11-05 20:28:22.525927	f	\N	{"matches": 8, "runs": 294, "batting_avg": 32.67, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 28.25, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_067	2025-11-05 20:28:22.526077	2025-11-06 09:28:58.735479	\N	0.98	2025-11-05 21:31:58.188002	f
aa4832cd-f0cf-44c1-a9f0-45ebe469ac15	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	AdvaySubhedar	batsman	25	2025-11-05 20:28:22.517135	f	\N	{"matches": 10, "runs": 236, "batting_avg": 26.22, "strike_rate": 0.0, "wickets": 12, "bowling_avg": 19.33, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_191	2025-11-05 20:28:22.517277	2025-11-06 09:28:58.73548	\N	0.98	2025-11-05 21:31:58.188004	f
aadedd0c-2aac-4f3f-a8d3-4bb6ba1c5d6f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	ShishirKapoor	bowler	25	2025-11-05 20:28:22.676489	f	\N	{"matches": 4, "runs": 26, "batting_avg": 26.0, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 28.89, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_379	2025-11-05 20:28:22.676634	2025-11-06 09:28:58.73548	\N	2.97	2025-11-05 21:31:58.188005	f
ab68e642-5b44-45e1-a496-bf5c0c52e442	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	JackMadgwick	batsman	25	2025-11-05 20:28:22.666347	f	\N	{"matches": 1, "runs": 221, "batting_avg": 36.83, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_562	2025-11-05 20:28:22.666494	2025-11-06 09:28:58.73548	\N	2.21	2025-11-05 21:31:58.188007	f
ab7321dd-fad2-4e4e-ad9c-287f4b8f2dea	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	FarhaanKhawaja	all-rounder	25	2025-11-05 20:28:22.323333	f	\N	{"matches": 1, "runs": 916, "batting_avg": 36.64, "strike_rate": 0.0, "wickets": 28, "bowling_avg": 24.64, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_070	2025-11-05 20:28:22.323643	2025-11-06 09:28:58.73548	\N	0.8	2025-11-05 21:31:58.188009	f
abe9d8e5-fa60-41d9-946f-3baaf6e96d4e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	AkhilDixit	bowler	25	2025-11-05 20:28:22.565684	f	\N	{"matches": 11, "runs": 27, "batting_avg": 3.86, "strike_rate": 0.0, "wickets": 17, "bowling_avg": 32.71, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_028	2025-11-05 20:28:22.565828	2025-11-06 09:28:58.73548	\N	1.11	2025-11-05 21:31:58.188015	f
ac257ee0-1945-4b05-a3b2-cd0dc1bfb9a3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	PuneetrajShivanand	all-rounder	25	2025-11-05 20:28:22.431051	f	\N	{"matches": 1, "runs": 416, "batting_avg": 24.47, "strike_rate": 0.0, "wickets": 12, "bowling_avg": 25.58, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_526	2025-11-05 20:28:22.431257	2025-11-06 09:28:58.735481	\N	0.95	2025-11-05 21:31:58.188021	f
ac2f9708-1558-4830-b368-b2e9dc056011	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	MukeshBhardwaj	all-rounder	25	2025-11-05 20:28:22.504373	f	\N	{"matches": 1, "runs": 86, "batting_avg": 10.75, "strike_rate": 0.0, "wickets": 20, "bowling_avg": 28.8, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_576	2025-11-05 20:28:22.504517	2025-11-06 09:28:58.735481	\N	0.98	2025-11-05 21:31:58.188022	f
ac6752b5-7e16-456f-b87c-1f4dcf423be0	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	AshanBunumusinghe	all-rounder	25	2025-11-05 20:28:22.6124	f	\N	{"matches": 1, "runs": 191, "batting_avg": 27.29, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 23.57, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_647	2025-11-05 20:28:22.612542	2025-11-06 09:28:58.735481	\N	1.32	2025-11-05 21:31:58.188033	f
ad062ff9-f7c6-446f-ae3b-16b34f4baff5	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	AntoniJanssen	batsman	25	2025-11-05 20:28:22.859848	f	\N	{"matches": 2, "runs": 4, "batting_avg": 2.0, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_163	2025-11-05 20:28:22.860026	2025-11-06 09:28:58.735481	\N	4.97	2025-11-05 21:31:58.188036	f
ad5acdcb-f6c9-408c-af7b-2d6eb502dbf3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	RajanGriowrirajan	all-rounder	25	2025-11-05 20:28:22.719562	f	\N	{"matches": 1, "runs": 41, "batting_avg": 5.86, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 51.86, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_269	2025-11-05 20:28:22.719714	2025-11-06 09:28:58.735481	\N	3.3	2025-11-05 21:31:58.188038	f
ad8f0f7f-4664-4131-8c58-4ba3dd9cacc0	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	RishaanFernandez	batsman	25	2025-11-05 20:28:22.673659	f	\N	{"matches": 3, "runs": 133, "batting_avg": 10.23, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 37.6, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_324	2025-11-05 20:28:22.673807	2025-11-06 09:28:58.735482	\N	2.62	2025-11-05 21:31:58.188039	f
ae7eaa9d-5d87-4968-827b-e0b3cf666ff5	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	PalasNuwal	all-rounder	25	2025-11-05 20:28:22.397632	f	\N	{"matches": 2, "runs": 513, "batting_avg": 17.1, "strike_rate": 0.0, "wickets": 13, "bowling_avg": 30.23, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_272	2025-11-05 20:28:22.39779	2025-11-06 09:28:58.735482	\N	0.92	2025-11-05 21:31:58.188051	f
aecae709-b658-49a9-babe-6dcfc0f1fdb8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	RokhanSafi	batsman	25	2025-11-05 20:28:22.758236	f	\N	{"matches": 3, "runs": 82, "batting_avg": 16.4, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 29.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_657	2025-11-05 20:28:22.758379	2025-11-06 09:28:58.735482	\N	3.69	2025-11-05 21:31:58.188052	f
af9292c1-22d9-4451-a894-169d3fe5ec0d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	CasperSchuijtvlot	bowler	25	2025-11-05 20:28:22.679244	f	\N	{"matches": 1, "runs": 24, "batting_avg": 12.0, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 15.33, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_493	2025-11-05 20:28:22.679389	2025-11-06 09:28:58.735482	\N	2.99	2025-11-05 21:31:58.188054	f
afd0f2d0-30d5-401f-b452-5c2decf8ed4a	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	PrabhakarAnbarasu	all-rounder	25	2025-11-05 20:28:22.495298	f	\N	{"matches": 1, "runs": 216, "batting_avg": 24.0, "strike_rate": 0.0, "wickets": 15, "bowling_avg": 23.67, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_721	2025-11-05 20:28:22.495443	2025-11-06 09:28:58.735482	\N	0.97	2025-11-05 21:31:58.188056	f
afeeeee2-d197-4a94-982e-3efeb2a29143	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	LucaBalducci	batsman	25	2025-11-05 20:28:22.419258	f	\N	{"matches": 1, "runs": 679, "batting_avg": 28.29, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 24.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_286	2025-11-05 20:28:22.419422	2025-11-06 09:28:58.735483	\N	0.93	2025-11-05 21:31:58.188057	f
b0b4b59c-4654-49df-8cc7-d5873f490dc8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	EhtishamAhmad	all-rounder	25	2025-11-05 20:28:22.416354	f	\N	{"matches": 2, "runs": 257, "batting_avg": 25.7, "strike_rate": 0.0, "wickets": 22, "bowling_avg": 24.82, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_401	2025-11-05 20:28:22.416514	2025-11-06 09:28:58.735483	\N	0.94	2025-11-05 21:31:58.188059	f
b1e2d711-a913-4913-a823-e2ed7334d0da	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	IshmeetSingh	batsman	25	2025-11-05 20:28:22.803478	f	\N	{"matches": 2, "runs": 45, "batting_avg": 11.25, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 47.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_344	2025-11-05 20:28:22.803638	2025-11-06 09:28:58.735483	\N	4.27	2025-11-05 21:31:58.188061	f
b1f4883e-4fe9-49ce-b49a-6b61f86cb64c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	ShayanMoodley	bowler	25	2025-11-05 20:28:22.507961	f	\N	{"matches": 2, "runs": 24, "batting_avg": 4.8, "strike_rate": 0.0, "wickets": 22, "bowling_avg": 21.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_399	2025-11-05 20:28:22.508116	2025-11-06 09:28:58.735483	\N	0.99	2025-11-05 21:31:58.188062	f
b2891ab9-f95a-4c40-a991-f6fdac5560da	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	ShreyTrehan	all-rounder	25	2025-11-05 20:28:22.432136	f	\N	{"matches": 2, "runs": 200, "batting_avg": 15.38, "strike_rate": 0.0, "wickets": 22, "bowling_avg": 26.86, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_355	2025-11-05 20:28:22.432288	2025-11-06 09:28:58.735483	\N	0.96	2025-11-05 21:31:58.188064	f
b294e3fa-2b7c-46ec-82ef-20266dcf355f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	MohseenKarche	batsman	25	2025-11-05 20:28:22.74525	f	\N	{"matches": 1, "runs": 153, "batting_avg": 15.3, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_329	2025-11-05 20:28:22.745402	2025-11-06 09:28:58.735484	\N	3.2	2025-11-05 21:31:58.188066	f
b2dfa044-3ae1-4790-a8ff-bc5f161370e5	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	JanBalk	batsman	25	2025-11-05 20:28:22.72862	f	\N	{"matches": 6, "runs": 106, "batting_avg": 35.33, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 56.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_151	2025-11-05 20:28:22.728761	2025-11-06 09:28:58.735484	\N	3.24	2025-11-05 21:31:58.188068	f
b2f51ee4-6716-4a03-abb5-a9ed86df2c94	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	MasoodKhan	all-rounder	25	2025-11-05 20:28:22.489972	f	\N	{"matches": 1, "runs": 264, "batting_avg": 22.0, "strike_rate": 0.0, "wickets": 13, "bowling_avg": 32.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_661	2025-11-05 20:28:22.490122	2025-11-06 09:28:58.735484	\N	0.97	2025-11-05 21:31:58.188071	f
b3092d39-00c9-4f56-b3c6-172d1523fdcc	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	ReinderLubbers	all-rounder	25	2025-11-05 20:28:22.415191	f	\N	{"matches": 1, "runs": 257, "batting_avg": 18.36, "strike_rate": 0.0, "wickets": 22, "bowling_avg": 20.55, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_043	2025-11-05 20:28:22.415391	2025-11-06 09:28:58.735484	\N	0.94	2025-11-05 21:31:58.188073	f
b3274fe1-7f86-4417-be3d-832acafccd3b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	MaheshNavale	all-rounder	25	2025-11-05 20:28:22.34845	f	\N	{"matches": 2, "runs": 692, "batting_avg": 38.44, "strike_rate": 0.0, "wickets": 18, "bowling_avg": 31.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_054	2025-11-05 20:28:22.348605	2025-11-06 09:28:58.735484	\N	0.87	2025-11-05 21:31:58.188075	f
b44d4ff3-0285-4638-bfd7-c8b2f46c0e97	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	SarukanKulasekaram	all-rounder	25	2025-11-05 20:28:22.492578	f	\N	{"matches": 2, "runs": 261, "batting_avg": 17.4, "strike_rate": 0.0, "wickets": 13, "bowling_avg": 25.23, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_347	2025-11-05 20:28:22.492731	2025-11-06 09:28:58.735484	\N	0.97	2025-11-05 21:31:58.188082	f
b4776d46-f3dc-4732-b3ee-5d9b29ce1a68	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	VihaanChatterji	bowler	25	2025-11-05 20:28:22.773855	f	\N	{"matches": 1, "runs": 10, "batting_avg": 5.0, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 13.2, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_726	2025-11-05 20:28:22.774067	2025-11-06 09:28:58.735485	\N	4.05	2025-11-05 21:31:58.188085	f
b4de57cc-bef6-41ec-bf5d-84032872e710	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	MahadAwan	bowler	25	2025-11-05 20:28:22.450813	f	\N	{"matches": 2, "runs": 40, "batting_avg": 8.0, "strike_rate": 0.0, "wickets": 27, "bowling_avg": 22.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_555	2025-11-05 20:28:22.450989	2025-11-06 09:28:58.735485	\N	0.97	2025-11-05 21:31:58.188086	f
b54db491-ce1b-4159-8a6b-bf16635de255	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	RehanWaheed	all-rounder	25	2025-11-05 20:28:22.367851	f	\N	{"matches": 1, "runs": 520, "batting_avg": 32.5, "strike_rate": 0.0, "wickets": 20, "bowling_avg": 21.6, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_370	2025-11-05 20:28:22.368024	2025-11-06 09:28:58.735485	\N	0.9	2025-11-05 21:31:58.188089	f
b5e8c1d8-7ff6-4d00-9a10-e3050823c66f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	HAMZA ANASIR	all-rounder	25	2025-11-05 20:28:22.532449	f	\N	{"matches": 1, "runs": 299, "batting_avg": 18.69, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 45.43, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_386	2025-11-05 20:28:22.532605	2025-11-06 09:28:58.735486	\N	0.98	2025-11-05 21:31:58.18809	f
b61c8da1-b6ad-48ee-9ba1-712bdbb13883	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	RafiRana	all-rounder	25	2025-11-05 20:28:22.454523	f	\N	{"matches": 1, "runs": 305, "batting_avg": 27.73, "strike_rate": 0.0, "wickets": 15, "bowling_avg": 12.4, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_430	2025-11-05 20:28:22.454669	2025-11-06 09:28:58.735486	\N	0.96	2025-11-05 21:31:58.188092	f
b6537d37-fcc2-4246-961d-4b0349feb6e2	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	JaapDickmann	batsman	25	2025-11-05 20:28:22.731734	f	\N	{"matches": 1, "runs": 161, "batting_avg": 32.2, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_525	2025-11-05 20:28:22.731889	2025-11-06 09:28:58.735486	\N	3.08	2025-11-05 21:31:58.188094	f
b71bbb33-6132-4f9e-bc64-e4eec47682e5	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	AroonJaved	batsman	25	2025-11-05 20:28:22.65322	f	\N	{"matches": 1, "runs": 213, "batting_avg": 12.53, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 23.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_618	2025-11-05 20:28:22.653361	2025-11-06 09:28:58.735486	\N	2.01	2025-11-05 21:31:58.188095	f
b7e0e8ee-8f9b-4173-9df0-caa83571c6d4	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	LiagetAnwar	all-rounder	25	2025-11-05 20:28:22.446235	f	\N	{"matches": 1, "runs": 363, "batting_avg": 30.25, "strike_rate": 0.0, "wickets": 13, "bowling_avg": 22.77, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_613	2025-11-05 20:28:22.446388	2025-11-06 09:28:58.735487	\N	0.95	2025-11-05 21:31:58.188098	f
b7f41f1b-a36f-40fb-a092-ce39edfa2b06	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	SidharthVenugopalan	batsman	25	2025-11-05 20:28:22.66826	f	\N	{"matches": 3, "runs": 161, "batting_avg": 20.13, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 30.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_097	2025-11-05 20:28:22.668407	2025-11-06 09:28:58.735487	\N	2.44	2025-11-05 21:31:58.1881	f
b8cabe1b-5d0d-47e7-aa69-37b8b561094e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	AmanBalasubramaniam	all-rounder	25	2025-11-05 20:28:22.499779	f	\N	{"matches": 1, "runs": 441, "batting_avg": 24.5, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 93.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_733	2025-11-05 20:28:22.49994	2025-11-06 09:28:58.735487	\N	0.97	2025-11-05 21:31:58.188102	f
b9f110ed-2902-43bf-8765-67cc822c24f8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	VinodDawra	batsman	25	2025-11-05 20:28:22.478598	f	\N	{"matches": 1, "runs": 519, "batting_avg": 27.32, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 78.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_563	2025-11-05 20:28:22.478835	2025-11-06 09:28:58.735487	\N	0.96	2025-11-05 21:31:58.188107	f
ba13c44b-6f7d-4519-b796-accfde5c76a3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	HejranAhmadi	batsman	25	2025-11-05 20:28:22.581163	f	\N	{"matches": 3, "runs": 259, "batting_avg": 19.92, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 57.67, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_063	2025-11-05 20:28:22.58131	2025-11-06 09:28:58.735487	\N	0.99	2025-11-05 21:31:58.188109	f
baed7f44-2b87-40b2-9304-dcfebb651f36	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	BalasubramaniamGurmurthy	all-rounder	25	2025-11-05 20:28:22.354127	f	\N	{"matches": 1, "runs": 127, "batting_avg": 9.07, "strike_rate": 0.0, "wickets": 42, "bowling_avg": 25.02, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_281	2025-11-05 20:28:22.354287	2025-11-06 09:28:58.735488	\N	0.91	2025-11-05 21:31:58.188112	f
bb2f1ba0-2ebe-493d-90f3-2e95af231acc	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	SuryaHenry	bowler	25	2025-11-05 20:28:22.79324	f	\N	{"matches": 1, "runs": 16, "batting_avg": 4.0, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 20.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_689	2025-11-05 20:28:22.793396	2025-11-06 09:28:58.735488	\N	4.22	2025-11-05 21:31:58.188114	f
bb7d1c51-685c-4a01-8e6f-d1ee2e085603	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	LonneBalk	batsman	25	2025-11-05 20:28:22.861681	f	\N	{"matches": 1, "runs": 3, "batting_avg": 3.0, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_455	2025-11-05 20:28:22.86184	2025-11-06 09:28:58.735488	\N	4.98	2025-11-05 21:31:58.188115	f
bbe1942d-4565-4594-959e-8a6d217b6d70	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	NishanthRamesh	all-rounder	25	2025-11-05 20:28:22.390639	f	\N	{"matches": 1, "runs": 358, "batting_avg": 27.54, "strike_rate": 0.0, "wickets": 23, "bowling_avg": 21.43, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_481	2025-11-05 20:28:22.3908	2025-11-06 09:28:58.735488	\N	0.92	2025-11-05 21:31:58.188117	f
bd302884-4bc3-4ab2-923e-ef2ca85292db	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	NiallRavi	bowler	25	2025-11-05 20:28:22.799443	f	\N	{"matches": 5, "runs": 6, "batting_avg": 1.5, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 34.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_194	2025-11-05 20:28:22.799599	2025-11-06 09:28:58.735488	\N	4.32	2025-11-05 21:31:58.188118	f
be1387b9-77b8-464a-bd52-28dd3d38c2e0	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	LouisCollignon	batsman	25	2025-11-05 20:28:22.698117	f	\N	{"matches": 2, "runs": 164, "batting_avg": 20.5, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 69.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_309	2025-11-05 20:28:22.698266	2025-11-06 09:28:58.735488	\N	2.72	2025-11-05 21:31:58.18812	f
be1578f7-33ae-4508-aa38-335b98f70e4a	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	BilalTayyab	batsman	25	2025-11-05 20:28:22.75178	f	\N	{"matches": 1, "runs": 111, "batting_avg": 18.5, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 28.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_433	2025-11-05 20:28:22.751939	2025-11-06 09:28:58.735489	\N	3.49	2025-11-05 21:31:58.188122	f
be74d414-4918-4d6c-b188-1e952ce3ea77	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	EdgarSchiferli	all-rounder	25	2025-11-05 20:28:22.488396	f	\N	{"matches": 2, "runs": 310, "batting_avg": 38.75, "strike_rate": 0.0, "wickets": 11, "bowling_avg": 15.73, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_168	2025-11-05 20:28:22.488552	2025-11-06 09:28:58.735489	\N	0.97	2025-11-05 21:31:58.188127	f
bf15117a-15e9-47a9-baf0-227e9d4e9db3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	RushaanShaikh	all-rounder	25	2025-11-05 20:28:22.60926	f	\N	{"matches": 1, "runs": 108, "batting_avg": 15.43, "strike_rate": 0.0, "wickets": 11, "bowling_avg": 20.82, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_651	2025-11-05 20:28:22.609409	2025-11-06 09:28:58.735489	\N	1.59	2025-11-05 21:31:58.18813	f
bf4aa208-5791-477a-82c1-012123f53380	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	SultanHaider	all-rounder	25	2025-11-05 20:28:22.434893	f	\N	{"matches": 1, "runs": 230, "batting_avg": 20.91, "strike_rate": 0.0, "wickets": 20, "bowling_avg": 28.35, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_581	2025-11-05 20:28:22.435049	2025-11-06 09:28:58.73549	\N	0.96	2025-11-05 21:31:58.188136	f
bf5149e6-8747-45d2-8e86-0107fed3740f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	OlafStadhouder	batsman	25	2025-11-05 20:28:22.816751	f	\N	{"matches": 1, "runs": 46, "batting_avg": 7.67, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 24.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_485	2025-11-05 20:28:22.816937	2025-11-06 09:28:58.73549	\N	4.42	2025-11-05 21:31:58.188138	f
bfb30809-f824-4aa4-a416-0ee72f236009	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	SanderHelberg	all-rounder	25	2025-11-05 20:28:22.365024	f	\N	{"matches": 2, "runs": 283, "batting_avg": 18.87, "strike_rate": 0.0, "wickets": 32, "bowling_avg": 23.94, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_246	2025-11-05 20:28:22.365171	2025-11-06 09:28:58.73549	\N	0.91	2025-11-05 21:31:58.188139	f
c18eaa7a-7249-493f-8dee-82971a27a7f2	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	SamanyuChauhan	all-rounder	25	2025-11-05 20:28:22.535846	f	\N	{"matches": 1, "runs": 190, "batting_avg": 21.11, "strike_rate": 0.0, "wickets": 12, "bowling_avg": 29.83, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_291	2025-11-05 20:28:22.536011	2025-11-06 09:28:58.73549	\N	0.99	2025-11-05 21:31:58.188146	f
c1d51fc1-766e-4f1a-a03c-2f7a61b64243	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	AbdulKhan	all-rounder	25	2025-11-05 20:28:22.617251	f	\N	{"matches": 1, "runs": 74, "batting_avg": 12.33, "strike_rate": 0.0, "wickets": 12, "bowling_avg": 22.67, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_290	2025-11-05 20:28:22.617395	2025-11-06 09:28:58.73549	\N	1.78	2025-11-05 21:31:58.188148	f
c284f130-d67e-4e80-ae7c-5efe69ea2c96	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	AvinashKumar	bowler	25	2025-11-05 20:28:22.802475	f	\N	{"matches": 3, "runs": 1, "batting_avg": 1.0, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 33.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_259	2025-11-05 20:28:22.802631	2025-11-06 09:28:58.73549	\N	4.36	2025-11-05 21:31:58.188149	f
c30d46e9-0ce5-4af0-ba6f-39cde01d05a3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	PaulHagebeuk	batsman	25	2025-11-05 20:28:22.856103	f	\N	{"matches": 2, "runs": 9, "batting_avg": 1.13, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_473	2025-11-05 20:28:22.856282	2025-11-06 09:28:58.735491	\N	4.92	2025-11-05 21:31:58.188154	f
c33a0794-a4bc-43a7-a6ec-7f22d40c61dc	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	JayantPote	batsman	25	2025-11-05 20:28:22.56748	f	\N	{"matches": 7, "runs": 377, "batting_avg": 34.27, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_013	2025-11-05 20:28:22.567623	2025-11-06 09:28:58.735491	\N	0.99	2025-11-05 21:31:58.188156	f
c3a698b4-fcbc-477a-b43c-f9eb1a8dfd21	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	AnthonyQuinn	bowler	25	2025-11-05 20:28:22.765616	f	\N	{"matches": 1, "runs": 23, "batting_avg": 7.67, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 35.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_254	2025-11-05 20:28:22.76576	2025-11-06 09:28:58.735491	\N	3.93	2025-11-05 21:31:58.188157	f
c3dfbb0b-4ca0-4ff6-bf1a-c330ed19106c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	QamarQazi	batsman	25	2025-11-05 20:28:22.813417	f	\N	{"matches": 1, "runs": 50, "batting_avg": 12.5, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 57.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_271	2025-11-05 20:28:22.813585	2025-11-06 09:28:58.735491	\N	4.38	2025-11-05 21:31:58.188161	f
c4e2f69b-3ef4-41d2-aab6-fde59e2a461b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	WaqasAhmad	bowler	25	2025-11-05 20:28:22.356206	f	\N	{"matches": 13, "runs": 291, "batting_avg": 48.5, "strike_rate": 0.0, "wickets": 34, "bowling_avg": 14.41, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_122	2025-11-05 20:28:22.356378	2025-11-06 09:28:58.735491	\N	0.9	2025-11-05 21:31:58.188162	f
c5ba1ad0-473f-4d73-8b9c-8840d26ca2c8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	SritharaNagamani	bowler	25	2025-11-05 20:28:22.730172	f	\N	{"matches": 2, "runs": 21, "batting_avg": 4.2, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 40.43, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_409	2025-11-05 20:28:22.730311	2025-11-06 09:28:58.735492	\N	3.48	2025-11-05 21:31:58.188168	f
c5d231cc-422c-4d83-adc3-9b9e7b8c1052	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	SeanEllicott	batsman	25	2025-11-05 20:28:22.58664	f	\N	{"matches": 3, "runs": 347, "batting_avg": 49.57, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_215	2025-11-05 20:28:22.586786	2025-11-06 09:28:58.735492	\N	0.99	2025-11-05 21:31:58.18817	f
c648bff0-431a-4c4b-867c-fbf27ff8fd66	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	WilkoFrieke	batsman	25	2025-11-05 20:28:22.855038	f	\N	{"matches": 1, "runs": 9, "batting_avg": 2.25, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_374	2025-11-05 20:28:22.855197	2025-11-06 09:28:58.735492	\N	4.92	2025-11-05 21:31:58.188172	f
c6c3f386-132c-405f-b087-61d92736ae2c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	SrivatsanSubbaraman	all-rounder	25	2025-11-05 20:28:22.521264	f	\N	{"matches": 2, "runs": 163, "batting_avg": 27.17, "strike_rate": 0.0, "wickets": 15, "bowling_avg": 18.6, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_180	2025-11-05 20:28:22.521407	2025-11-06 09:28:58.735492	\N	0.98	2025-11-05 21:31:58.188173	f
c720b315-fc3d-4918-ba2f-8cf99f1923ac	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	ZishaanYousaf	all-rounder	25	2025-11-05 20:28:22.544687	f	\N	{"matches": 1, "runs": 363, "batting_avg": 21.35, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 42.33, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_673	2025-11-05 20:28:22.544839	2025-11-06 09:28:58.735492	\N	0.98	2025-11-05 21:31:58.188175	f
c904bf4f-908f-448e-a4b7-deac874e32d0	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	AtulRana	batsman	25	2025-11-05 20:28:22.769392	f	\N	{"matches": 1, "runs": 115, "batting_avg": 115.0, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_229	2025-11-05 20:28:22.769546	2025-11-06 09:28:58.735493	\N	3.75	2025-11-05 21:31:58.188187	f
c989d47f-7022-4206-9fef-bbee5c33e546	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	AnujPatel	all-rounder	25	2025-11-05 20:28:22.655528	f	\N	{"matches": 1, "runs": 119, "batting_avg": 39.67, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 30.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_137	2025-11-05 20:28:22.655691	2025-11-06 09:28:58.735493	\N	2.36	2025-11-05 21:31:58.188191	f
ca482983-b014-4f20-9ac4-218d9193aed5	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	SarangaLiyanage	all-rounder	25	2025-11-05 20:28:22.386908	f	\N	{"matches": 1, "runs": 544, "batting_avg": 23.65, "strike_rate": 0.0, "wickets": 15, "bowling_avg": 19.87, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_331	2025-11-05 20:28:22.387062	2025-11-06 09:28:58.735493	\N	0.91	2025-11-05 21:31:58.188199	f
cac2cfd6-d5a6-4e6f-9bc1-d0b99d181320	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	FrancoiseStoman	all-rounder	25	2025-11-05 20:28:22.381535	f	\N	{"matches": 1, "runs": 231, "batting_avg": 17.77, "strike_rate": 0.0, "wickets": 31, "bowling_avg": 18.52, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_668	2025-11-05 20:28:22.381685	2025-11-06 09:28:58.735493	\N	0.92	2025-11-05 21:31:58.188201	f
cb7a4acf-14b0-471e-8820-48a144e9daa4	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	AvinashAkella	all-rounder	25	2025-11-05 20:28:22.475258	f	\N	{"matches": 1, "runs": 65, "batting_avg": 7.22, "strike_rate": 0.0, "wickets": 23, "bowling_avg": 31.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_125	2025-11-05 20:28:22.475486	2025-11-06 09:28:58.735494	\N	0.98	2025-11-05 21:31:58.188202	f
cc3435a4-0db5-4fed-8fab-d235f2e59e0c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	ZeeshanChoudhry	all-rounder	25	2025-11-05 20:28:22.536749	f	\N	{"matches": 1, "runs": 54, "batting_avg": 7.71, "strike_rate": 0.0, "wickets": 18, "bowling_avg": 30.89, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_570	2025-11-05 20:28:22.536913	2025-11-06 09:28:58.735494	\N	0.99	2025-11-05 21:31:58.188204	f
cd381471-5593-4a5d-81fa-943ba68b58a7	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	SagarParihar	all-rounder	25	2025-11-05 20:28:22.624216	f	\N	{"matches": 1, "runs": 134, "batting_avg": 9.57, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 43.22, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_706	2025-11-05 20:28:22.624357	2025-11-06 09:28:58.735494	\N	1.68	2025-11-05 21:31:58.188208	f
cd828faf-cba5-4099-bc65-af64df655155	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	JeroenBal	batsman	25	2025-11-05 20:28:22.690527	f	\N	{"matches": 2, "runs": 203, "batting_avg": 18.45, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_354	2025-11-05 20:28:22.690789	2025-11-06 09:28:58.735494	\N	2.47	2025-11-05 21:31:58.188209	f
ce363d95-b3ca-4b71-800f-43f99fc01c83	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	ZidaneHamid	batsman	25	2025-11-05 20:28:22.843202	f	\N	{"matches": 1, "runs": 14, "batting_avg": 3.5, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 113.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_599	2025-11-05 20:28:22.843361	2025-11-06 09:28:58.735494	\N	4.72	2025-11-05 21:31:58.188212	f
d004c2cc-7812-4f5e-98d3-5bd4538d6752	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	SawanVelidandla	batsman	25	2025-11-05 20:28:22.517852	f	\N	{"matches": 8, "runs": 171, "batting_avg": 13.15, "strike_rate": 0.0, "wickets": 15, "bowling_avg": 23.2, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_175	2025-11-05 20:28:22.518004	2025-11-06 09:28:58.735495	\N	0.98	2025-11-05 21:31:58.188214	f
d195f2e3-0eab-49e8-8c9b-cd2585746899	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	AahilPenubolu	batsman	25	2025-11-05 20:28:22.80148	f	\N	{"matches": 1, "runs": 46, "batting_avg": 7.67, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 68.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_696	2025-11-05 20:28:22.801637	2025-11-06 09:28:58.735495	\N	4.26	2025-11-05 21:31:58.188219	f
d2072191-5b2f-465c-b96f-08983b09dcc1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	HarrySingh	batsman	25	2025-11-05 20:28:22.346526	f	\N	{"matches": 11, "runs": 488, "batting_avg": 25.68, "strike_rate": 0.0, "wickets": 29, "bowling_avg": 19.34, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_056	2025-11-05 20:28:22.346688	2025-11-06 09:28:58.735495	\N	0.88	2025-11-05 21:31:58.188222	f
d2ea9de5-17dd-4cf0-bcad-9ccab5c1b5d9	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	FarhanAhmed	bowler	25	2025-11-05 20:28:22.778358	f	\N	{"matches": 1, "runs": 2, "batting_avg": 2.0, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 23.6, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_585	2025-11-05 20:28:22.778516	2025-11-06 09:28:58.735495	\N	4.12	2025-11-05 21:31:58.188224	f
d3682c40-056c-4d7c-89dc-317b5c33fecf	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	IrfanYounis	batsman	25	2025-11-05 20:28:22.844301	f	\N	{"matches": 2, "runs": 13, "batting_avg": 13.0, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 46.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_295	2025-11-05 20:28:22.844469	2025-11-06 09:28:58.735496	\N	4.73	2025-11-05 21:31:58.188226	f
d386b8a1-02f1-4ac1-9ead-5fc1377e1993	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	AvyuktVats	bowler	25	2025-11-05 20:28:22.80652	f	\N	{"matches": 1, "runs": 18, "batting_avg": 0.0, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 21.67, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_529	2025-11-05 20:28:22.806744	2025-11-06 09:28:58.735496	\N	4.36	2025-11-05 21:31:58.188227	f
d4c75d73-d025-4bdd-97be-fd959a5ebca5	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	EthanHartsink	all-rounder	25	2025-11-05 20:28:22.693104	f	\N	{"matches": 1, "runs": 50, "batting_avg": 10.0, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 30.63, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_389	2025-11-05 20:28:22.693273	2025-11-06 09:28:58.735496	\N	2.98	2025-11-05 21:31:58.188234	f
d4f4adc2-4937-4c20-857f-5b656acd99f2	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	AhmedMasharaf	all-rounder	25	2025-11-05 20:28:22.672751	f	\N	{"matches": 1, "runs": 35, "batting_avg": 11.67, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 42.11, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_594	2025-11-05 20:28:22.672909	2025-11-06 09:28:58.735496	\N	2.89	2025-11-05 21:31:58.188235	f
d51b3edf-36b6-426d-9951-5502531db4b2	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	WaliedZamani	all-rounder	25	2025-11-05 20:28:22.715282	f	\N	{"matches": 1, "runs": 135, "batting_avg": 13.5, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 42.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_403	2025-11-05 20:28:22.715429	2025-11-06 09:28:58.735496	\N	2.98	2025-11-05 21:31:58.188241	f
d6015955-139f-4b4f-bd59-38c42d485142	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	SidanthRajaraman	batsman	25	2025-11-05 20:28:22.854031	f	\N	{"matches": 1, "runs": 18, "batting_avg": 3.6, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_441	2025-11-05 20:28:22.854187	2025-11-06 09:28:58.735497	\N	4.84	2025-11-05 21:31:58.188247	f
d6bcd647-3bfd-4e72-b74f-1ae4a2f2cc18	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	PraveenkumarAlluri	all-rounder	25	2025-11-05 20:28:22.508881	f	\N	{"matches": 1, "runs": 47, "batting_avg": 15.67, "strike_rate": 0.0, "wickets": 21, "bowling_avg": 17.1, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_552	2025-11-05 20:28:22.509032	2025-11-06 09:28:58.735497	\N	0.99	2025-11-05 21:31:58.188248	f
d6dde139-c658-48b6-9dba-3477802bf55a	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	UsmanYounas	all-rounder	25	2025-11-05 20:28:22.621843	f	\N	{"matches": 1, "runs": 37, "batting_avg": 18.5, "strike_rate": 0.0, "wickets": 13, "bowling_avg": 23.31, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_408	2025-11-05 20:28:22.622009	2025-11-06 09:28:58.735497	\N	1.95	2025-11-05 21:31:58.18825	f
d7460b50-c8b2-40f7-8983-662c4c14146d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	SharadHake	all-rounder	25	2025-11-05 20:28:22.395699	f	\N	{"matches": 1, "runs": 78, "batting_avg": 6.0, "strike_rate": 0.0, "wickets": 34, "bowling_avg": 16.47, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_383	2025-11-05 20:28:22.395886	2025-11-06 09:28:58.735497	\N	0.94	2025-11-05 21:31:58.188252	f
d7b39622-e449-4542-9230-e3e73ea223fe	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	ShrihanPisal	all-rounder	25	2025-11-05 20:28:22.783639	f	\N	{"matches": 1, "runs": 48, "batting_avg": 9.6, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 60.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_227	2025-11-05 20:28:22.783799	2025-11-06 09:28:58.735498	\N	4.08	2025-11-05 21:31:58.188254	f
d84e5acc-d9cd-486a-8899-d2fd0e2f2ef6	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	SagarMahangoe	all-rounder	25	2025-11-05 20:28:22.648554	f	\N	{"matches": 1, "runs": 120, "batting_avg": 10.91, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 34.38, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_303	2025-11-05 20:28:22.648696	2025-11-06 09:28:58.735498	\N	2.11	2025-11-05 21:31:58.188256	f
d8564052-7605-4751-b09c-682c0370fef2	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	DanishMunir	bowler	25	2025-11-05 20:28:22.62666	f	\N	{"matches": 1, "runs": 24, "batting_avg": 6.0, "strike_rate": 0.0, "wickets": 13, "bowling_avg": 27.08, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_261	2025-11-05 20:28:22.626802	2025-11-06 09:28:58.735498	\N	2.07	2025-11-05 21:31:58.188258	f
d942fda1-4e4b-4c03-ac7c-5fa39bed181b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	AryanAjjarapu	batsman	25	2025-11-05 20:28:22.815699	f	\N	{"matches": 1, "runs": 46, "batting_avg": 5.75, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 189.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_411	2025-11-05 20:28:22.815864	2025-11-06 09:28:58.735498	\N	4.42	2025-11-05 21:31:58.188264	f
da36080d-5101-4a5d-b0ef-856cb24044e6	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	JordanWoolf	all-rounder	25	2025-11-05 20:28:22.439514	f	\N	{"matches": 1, "runs": 390, "batting_avg": 24.38, "strike_rate": 0.0, "wickets": 12, "bowling_avg": 26.83, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_534	2025-11-05 20:28:22.439701	2025-11-06 09:28:58.735498	\N	0.95	2025-11-05 21:31:58.188268	f
db3d693f-3e13-4b0d-90a6-609219157438	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	KarthikPrakash	batsman	25	2025-11-05 20:28:22.520354	f	\N	{"matches": 8, "runs": 313, "batting_avg": 24.08, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 29.63, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_120	2025-11-05 20:28:22.520498	2025-11-06 09:28:58.735499	\N	0.98	2025-11-05 21:31:58.188271	f
db557db8-edc8-4c29-98b7-c66eb71e3a22	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	SivaGoma	bowler	25	2025-11-05 20:28:22.845425	f	\N	{"matches": 1, "runs": 6, "batting_avg": 3.0, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 27.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_233	2025-11-05 20:28:22.845587	2025-11-06 09:28:58.735499	\N	4.79	2025-11-05 21:31:58.188273	f
dc21bec6-540e-40c4-b999-13a1ef94d311	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	DanielRawson	all-rounder	25	2025-11-05 20:28:22.392902	f	\N	{"matches": 2, "runs": 105, "batting_avg": 8.75, "strike_rate": 0.0, "wickets": 34, "bowling_avg": 21.91, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_449	2025-11-05 20:28:22.393068	2025-11-06 09:28:58.735499	\N	0.94	2025-11-05 21:31:58.188274	f
dceb1157-9081-4b1e-8908-2a86a8a08d09	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	ShivankSingh	all-rounder	25	2025-11-05 20:28:22.755494	f	\N	{"matches": 1, "runs": 45, "batting_avg": 7.5, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 27.8, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_551	2025-11-05 20:28:22.755639	2025-11-06 09:28:58.735499	\N	3.72	2025-11-05 21:31:58.188277	f
dd1a0b5d-49ed-4fa2-b159-1106e07058cf	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	ShreyasPotdar	all-rounder	25	2025-11-05 20:28:22.49623	f	\N	{"matches": 1, "runs": 277, "batting_avg": 15.39, "strike_rate": 0.0, "wickets": 12, "bowling_avg": 29.17, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_336	2025-11-05 20:28:22.496376	2025-11-06 09:28:58.735499	\N	0.97	2025-11-05 21:31:58.188279	f
dd4ca219-92e5-462c-933f-6433959b4bbd	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	WaseemKhan	all-rounder	25	2025-11-05 20:28:22.437672	f	\N	{"matches": 1, "runs": 67, "batting_avg": 11.17, "strike_rate": 0.0, "wickets": 27, "bowling_avg": 16.19, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_722	2025-11-05 20:28:22.437828	2025-11-06 09:28:58.735499	\N	0.96	2025-11-05 21:31:58.188282	f
dda46009-8890-4755-aac0-9ec325805855	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	AbhishekSaxena	bowler	25	2025-11-05 20:28:22.402205	f	\N	{"matches": 10, "runs": 209, "batting_avg": 13.06, "strike_rate": 0.0, "wickets": 27, "bowling_avg": 17.44, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_193	2025-11-05 20:28:22.40235	2025-11-06 09:28:58.7355	\N	0.94	2025-11-05 21:31:58.188284	f
ddc39f03-d0ca-4c0d-ac9c-d68a336ec99f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	RosalieLawrence	all-rounder	25	2025-11-05 20:28:22.423997	f	\N	{"matches": 1, "runs": 604, "batting_avg": 31.79, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 8.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_192	2025-11-05 20:28:22.424154	2025-11-06 09:28:58.7355	\N	0.93	2025-11-05 21:31:58.188286	f
de932f67-511c-4489-a407-4a4aa77e2d58	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	KirtiSingh	bowler	25	2025-11-05 20:28:22.848752	f	\N	{"matches": 3, "runs": 3, "batting_avg": 1.5, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 8.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_204	2025-11-05 20:28:22.848931	2025-11-06 09:28:58.7355	\N	4.82	2025-11-05 21:31:58.188287	f
deb5cf75-a953-4507-96c5-ab68dedcbd90	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	AdnanShah	batsman	25	2025-11-05 20:28:22.470398	f	\N	{"matches": 1, "runs": 547, "batting_avg": 32.18, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_565	2025-11-05 20:28:22.470541	2025-11-06 09:28:58.7355	\N	0.95	2025-11-05 21:31:58.188289	f
df09ab42-49d9-4656-aa9b-cbf35fb6ecad	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	SakethReddy	all-rounder	25	2025-11-05 20:28:22.584801	f	\N	{"matches": 2, "runs": 119, "batting_avg": 14.88, "strike_rate": 0.0, "wickets": 12, "bowling_avg": 40.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_487	2025-11-05 20:28:22.584962	2025-11-06 09:28:58.7355	\N	1.2	2025-11-05 21:31:58.188291	f
dfca9b5a-eac3-4bfc-b8fb-cf874d1f6d84	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	MickBoendermaker	all-rounder	25	2025-11-05 20:28:22.440778	f	\N	{"matches": 3, "runs": 304, "batting_avg": 15.2, "strike_rate": 0.0, "wickets": 16, "bowling_avg": 29.56, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_053	2025-11-05 20:28:22.440979	2025-11-06 09:28:58.735501	\N	0.95	2025-11-05 21:31:58.188292	f
e0598344-f940-4230-85b1-1bae8438b0e3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	NoorAhmed	all-rounder	25	2025-11-05 20:28:22.702039	f	\N	{"matches": 1, "runs": 32, "batting_avg": 0.0, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 10.25, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_443	2025-11-05 20:28:22.702194	2025-11-06 09:28:58.735501	\N	3.15	2025-11-05 21:31:58.188296	f
e08a0b13-4bf6-4853-8d72-84273821e0c3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	ArrushNadakatta	all-rounder	25	2025-11-05 20:28:22.328155	f	\N	{"matches": 12, "runs": 525, "batting_avg": 25.0, "strike_rate": 0.0, "wickets": 44, "bowling_avg": 14.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_145	2025-11-05 20:28:22.328383	2025-11-06 09:28:58.735501	\N	0.82	2025-11-05 21:31:58.188297	f
e0dab0c2-2537-4af1-9319-458e89b929a3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	HelalGhairat	all-rounder	25	2025-11-05 20:28:22.52684	f	\N	{"matches": 1, "runs": 121, "batting_avg": 12.1, "strike_rate": 0.0, "wickets": 16, "bowling_avg": 25.63, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_489	2025-11-05 20:28:22.52701	2025-11-06 09:28:58.735501	\N	0.99	2025-11-05 21:31:58.188299	f
e1f526dc-b2a1-42cc-97ce-2ed7006be71a	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	SourabhJain	all-rounder	25	2025-11-05 20:28:22.500655	f	\N	{"matches": 1, "runs": 161, "batting_avg": 23.0, "strike_rate": 0.0, "wickets": 17, "bowling_avg": 29.59, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_477	2025-11-05 20:28:22.500802	2025-11-06 09:28:58.735501	\N	0.98	2025-11-05 21:31:58.188302	f
e202b57a-e156-4bc4-a4d3-a6fe53b0182f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	AdiDimri	all-rounder	25	2025-11-05 20:28:22.38061	f	\N	{"matches": 4, "runs": 575, "batting_avg": 26.14, "strike_rate": 0.0, "wickets": 15, "bowling_avg": 27.2, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_058	2025-11-05 20:28:22.380767	2025-11-06 09:28:58.735502	\N	0.9	2025-11-05 21:31:58.188304	f
e20f4d9d-39c4-4e82-8fc8-adf6f56aac0c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	UsmanYousaf	all-rounder	25	2025-11-05 20:28:22.4066	f	\N	{"matches": 2, "runs": 374, "batting_avg": 24.93, "strike_rate": 0.0, "wickets": 18, "bowling_avg": 28.72, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_334	2025-11-05 20:28:22.406744	2025-11-06 09:28:58.735502	\N	0.93	2025-11-05 21:31:58.188305	f
e2125da8-923e-415d-8631-3d079bd6b5af	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	AkhilGolla	batsman	25	2025-11-05 20:28:22.650891	f	\N	{"matches": 2, "runs": 258, "batting_avg": 25.8, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_118	2025-11-05 20:28:22.651032	2025-11-06 09:28:58.735502	\N	1.68	2025-11-05 21:31:58.188307	f
e2467f93-bc90-4426-9a26-a9a26a128a34	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	NissarAli	all-rounder	25	2025-11-05 20:28:22.459849	f	\N	{"matches": 2, "runs": 420, "batting_avg": 21.0, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 36.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_044	2025-11-05 20:28:22.460014	2025-11-06 09:28:58.735503	\N	0.95	2025-11-05 21:31:58.188308	f
e269179a-3b93-4e4d-89cd-0cd4e8e8193d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	SunilSarangi	batsman	25	2025-11-05 20:28:22.487413	f	\N	{"matches": 1, "runs": 520, "batting_avg": 32.5, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_459	2025-11-05 20:28:22.487586	2025-11-06 09:28:58.735503	\N	0.96	2025-11-05 21:31:58.18831	f
e278c570-2e76-4b6e-94eb-7d5c09ee0e70	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	WalterHolleman	batsman	25	2025-11-05 20:28:22.74621	f	\N	{"matches": 2, "runs": 150, "batting_avg": 21.43, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_335	2025-11-05 20:28:22.746356	2025-11-06 09:28:58.735503	\N	3.24	2025-11-05 21:31:58.188316	f
e297ded2-777e-4f62-b2d0-b93ae80e7269	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	LukasKuper	all-rounder	25	2025-11-05 20:28:22.727822	f	\N	{"matches": 1, "runs": 108, "batting_avg": 12.0, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 36.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_252	2025-11-05 20:28:22.727982	2025-11-06 09:28:58.735503	\N	3.21	2025-11-05 21:31:58.188319	f
e4ea05c6-ca6e-4c40-8a39-0c2d363e868d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	ManinderBisen	bowler	25	2025-11-05 20:28:22.464556	f	\N	{"matches": 9, "runs": 131, "batting_avg": 14.56, "strike_rate": 0.0, "wickets": 22, "bowling_avg": 19.41, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_148	2025-11-05 20:28:22.464705	2025-11-06 09:28:58.735503	\N	0.97	2025-11-05 21:31:58.18832	f
e4f3363a-672c-4cce-8a6a-a2c09ad62c34	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	GijsKuijstermans	all-rounder	25	2025-11-05 20:28:22.760123	f	\N	{"matches": 1, "runs": 33, "batting_avg": 5.5, "strike_rate": 0.0, "wickets": 5, "bowling_avg": 61.8, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_484	2025-11-05 20:28:22.760265	2025-11-06 09:28:58.735504	\N	3.83	2025-11-05 21:31:58.188322	f
e54276b4-aadb-4a92-ae26-da1dbf1c431a	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	ShadabSarwary	all-rounder	25	2025-11-05 20:28:22.337424	f	\N	{"matches": 1, "runs": 816, "batting_avg": 45.33, "strike_rate": 0.0, "wickets": 20, "bowling_avg": 24.1, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_453	2025-11-05 20:28:22.33759	2025-11-06 09:28:58.735504	\N	0.84	2025-11-05 21:31:58.188324	f
e55f45c6-b6e1-421c-967a-c9ed50af23e5	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	TiboBalk	bowler	25	2025-11-05 20:28:22.497108	f	\N	{"matches": 6, "runs": 126, "batting_avg": 11.45, "strike_rate": 0.0, "wickets": 19, "bowling_avg": 14.26, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_208	2025-11-05 20:28:22.497257	2025-11-06 09:28:58.735504	\N	0.98	2025-11-05 21:31:58.188325	f
e6eca08a-a0b8-410a-a329-58fe36733399	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	SultanKhan	all-rounder	25	2025-11-05 20:28:22.358171	f	\N	{"matches": 2, "runs": 324, "batting_avg": 20.25, "strike_rate": 0.0, "wickets": 32, "bowling_avg": 22.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_643	2025-11-05 20:28:22.358353	2025-11-06 09:28:58.735504	\N	0.9	2025-11-05 21:31:58.18833	f
e7ab6301-c7af-439f-8b62-4baa67396bf8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	GuyPathak	batsman	25	2025-11-05 20:28:22.686569	f	\N	{"matches": 7, "runs": 77, "batting_avg": 15.4, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 29.43, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_144	2025-11-05 20:28:22.687261	2025-11-06 09:28:58.735505	\N	2.9	2025-11-05 21:31:58.188337	f
e84013e3-06a1-4959-91f0-1eaba55c329b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	LucaPucciatti	all-rounder	25	2025-11-05 20:28:22.501607	f	\N	{"matches": 1, "runs": 93, "batting_avg": 4.43, "strike_rate": 0.0, "wickets": 20, "bowling_avg": 31.35, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_391	2025-11-05 20:28:22.501752	2025-11-06 09:28:58.735505	\N	0.98	2025-11-05 21:31:58.188338	f
e9b86a07-574e-4d63-b226-8b5e060d109d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	JuanFourie	all-rounder	25	2025-11-05 20:28:22.398582	f	\N	{"matches": 1, "runs": 577, "batting_avg": 41.21, "strike_rate": 0.0, "wickets": 10, "bowling_avg": 34.4, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_384	2025-11-05 20:28:22.398732	2025-11-06 09:28:58.735505	\N	0.92	2025-11-05 21:31:58.188342	f
ea96f3c4-e1a0-4577-8165-4382e73a8c6e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	NavyahRajesh	all-rounder	25	2025-11-05 20:28:22.570977	f	\N	{"matches": 1, "runs": 51, "batting_avg": 6.38, "strike_rate": 0.0, "wickets": 16, "bowling_avg": 28.56, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_462	2025-11-05 20:28:22.571121	2025-11-06 09:28:58.735505	\N	1.12	2025-11-05 21:31:58.188345	f
eafc47f0-50f9-40e9-af3e-b9fbd8b24d75	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	VaibhavVakharia	all-rounder	25	2025-11-05 20:28:22.368944	f	\N	{"matches": 1, "runs": 634, "batting_avg": 42.27, "strike_rate": 0.0, "wickets": 14, "bowling_avg": 27.14, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_210	2025-11-05 20:28:22.369117	2025-11-06 09:28:58.735505	\N	0.9	2025-11-05 21:31:58.188346	f
eb75d0a0-8eef-4790-8f50-d7172155e862	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	EzzatMuhseni	batsman	25	2025-11-05 20:28:22.548473	f	\N	{"matches": 8, "runs": 256, "batting_avg": 23.27, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 28.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_154	2025-11-05 20:28:22.548643	2025-11-06 09:28:58.735506	\N	0.99	2025-11-05 21:31:58.188348	f
eb8e1486-6485-4353-8ae9-9ddb36c7d924	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	AbdullahSafi	bowler	25	2025-11-05 20:28:22.506118	f	\N	{"matches": 2, "runs": 58, "batting_avg": 9.67, "strike_rate": 0.0, "wickets": 21, "bowling_avg": 27.05, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_463	2025-11-05 20:28:22.506262	2025-11-06 09:28:58.735506	\N	0.98	2025-11-05 21:31:58.18835	f
eb8fe79b-c145-4c02-835d-b2f0cb051973	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	ShitizArya	bowler	25	2025-11-05 20:28:22.707721	f	\N	{"matches": 2, "runs": 26, "batting_avg": 8.67, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 48.88, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_298	2025-11-05 20:28:22.707862	2025-11-06 09:28:58.735506	\N	3.2	2025-11-05 21:31:58.188352	f
ed0c44b5-47bc-458d-b05c-e85eadca8e81	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	ViswanathanRaman	all-rounder	25	2025-11-05 20:28:22.400408	f	\N	{"matches": 2, "runs": 190, "batting_avg": 21.11, "strike_rate": 0.0, "wickets": 28, "bowling_avg": 14.57, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_147	2025-11-05 20:28:22.400561	2025-11-06 09:28:58.735506	\N	0.94	2025-11-05 21:31:58.188355	f
ed4d7980-c2e6-4dfd-b1cf-f1d775674765	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	ThomasQuayle	all-rounder	25	2025-11-05 20:28:22.737231	f	\N	{"matches": 1, "runs": 46, "batting_avg": 9.2, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 15.17, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_573	2025-11-05 20:28:22.737379	2025-11-06 09:28:58.735506	\N	3.48	2025-11-05 21:31:58.188356	f
ee32a692-e443-4cd4-b8eb-6759ee91e383	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	MuhammadYaseen	batsman	25	2025-11-05 20:28:22.572739	f	\N	{"matches": 1, "runs": 343, "batting_avg": 14.91, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 30.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_179	2025-11-05 20:28:22.572895	2025-11-06 09:28:58.735507	\N	0.99	2025-11-05 21:31:58.188361	f
ee3fbb3b-1324-402d-a12b-58e3b8274229	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	GeronimoNota	all-rounder	25	2025-11-05 20:28:22.458101	f	\N	{"matches": 1, "runs": 273, "batting_avg": 17.06, "strike_rate": 0.0, "wickets": 16, "bowling_avg": 27.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_648	2025-11-05 20:28:22.458246	2025-11-06 09:28:58.735507	\N	0.96	2025-11-05 21:31:58.188363	f
eeaf814f-2746-4830-969f-21fb21bf79df	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	MihirGoyal	all-rounder	25	2025-11-05 20:28:22.449807	f	\N	{"matches": 2, "runs": 290, "batting_avg": 29.0, "strike_rate": 0.0, "wickets": 16, "bowling_avg": 16.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_039	2025-11-05 20:28:22.449986	2025-11-06 09:28:58.735507	\N	0.96	2025-11-05 21:31:58.188364	f
f0134f34-1e33-446f-958c-0e06ff34c6bc	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	AsadMalik	batsman	25	2025-11-05 20:28:22.863701	f	\N	{"matches": 1, "runs": 1, "batting_avg": 1.0, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_626	2025-11-05 20:28:22.863864	2025-11-06 09:28:58.735507	\N	5	2025-11-05 21:31:58.188372	f
f217413c-ae14-47f0-9196-582642ab5c08	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	MichaelDukker	bowler	25	2025-11-05 20:28:22.592935	f	\N	{"matches": 7, "runs": 83, "batting_avg": 16.6, "strike_rate": 0.0, "wickets": 13, "bowling_avg": 18.85, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_223	2025-11-05 20:28:22.593078	2025-11-06 09:28:58.735507	\N	1.44	2025-11-05 21:31:58.188376	f
f2bf421c-0245-47e9-869d-807026e2480a	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	HaiderAli	batsman	25	2025-11-05 20:28:22.821289	f	\N	{"matches": 5, "runs": 61, "batting_avg": 15.25, "strike_rate": 0.0, "wickets": 0, "bowling_avg": 0.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_091	2025-11-05 20:28:22.821506	2025-11-06 09:28:58.735508	\N	4.41	2025-11-05 21:31:58.188378	f
f30fb360-c85b-4a09-9bcd-d9abac9e50c8	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	FezanFirdausi	batsman	25	2025-11-05 20:28:22.789818	f	\N	{"matches": 3, "runs": 40, "batting_avg": 5.71, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 51.67, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_499	2025-11-05 20:28:22.790104	2025-11-06 09:28:58.735508	\N	4.16	2025-11-05 21:31:58.188379	f
f34a7040-63a4-4e06-9ec1-cefdf89f5086	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	AbhinandhanDevadiga	all-rounder	25	2025-11-05 20:28:22.378675	f	\N	{"matches": 2, "runs": 346, "batting_avg": 38.44, "strike_rate": 0.0, "wickets": 26, "bowling_avg": 26.12, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_010	2025-11-05 20:28:22.378838	2025-11-06 09:28:58.735508	\N	0.92	2025-11-05 21:31:58.188381	f
f3faed0b-0f48-471c-b0d5-9efc6300226b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	JamesRidley	all-rounder	25	2025-11-05 20:28:22.62742	f	\N	{"matches": 1, "runs": 51, "batting_avg": 12.75, "strike_rate": 0.0, "wickets": 12, "bowling_avg": 16.42, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_066	2025-11-05 20:28:22.627561	2025-11-06 09:28:58.735508	\N	2.04	2025-11-05 21:31:58.188382	f
f530f943-4335-4fe2-9341-a41e1f00e72f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	SrinathPanchavati	bowler	25	2025-11-05 20:28:22.739074	f	\N	{"matches": 1, "runs": 13, "batting_avg": 13.0, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 15.57, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_574	2025-11-05 20:28:22.739219	2025-11-06 09:28:58.735508	\N	3.56	2025-11-05 21:31:58.188389	f
f557ae10-7f06-45f2-afa5-4a50dce0137e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	PhilipHeeremans	bowler	25	2025-11-05 20:28:22.822396	f	\N	{"matches": 1, "runs": 19, "batting_avg": 6.33, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 63.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_249	2025-11-05 20:28:22.822582	2025-11-06 09:28:58.735509	\N	4.51	2025-11-05 21:31:58.188391	f
f5cd4aac-66fa-4730-aff0-96ca3fcf5d6e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	MethmalJayasekara	all-rounder	25	2025-11-05 20:28:22.549444	f	\N	{"matches": 1, "runs": 296, "batting_avg": 21.14, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 43.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_116	2025-11-05 20:28:22.549595	2025-11-06 09:28:58.735509	\N	0.99	2025-11-05 21:31:58.188392	f
f5f7c630-eaaf-46dd-85e5-2cacc97a996b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	413865ef-caa0-467d-a1fe-e022abc360a0	HimanshuPant	all-rounder	25	2025-11-05 20:28:22.438579	f	\N	{"matches": 1, "runs": 305, "batting_avg": 25.42, "strike_rate": 0.0, "wickets": 16, "bowling_avg": 20.19, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_406	2025-11-05 20:28:22.438729	2025-11-06 09:28:58.735509	\N	0.95	2025-11-05 21:31:58.188394	f
f6456e3c-d439-49f1-92ad-ca1407e80632	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	ThomasSpits	all-rounder	25	2025-11-05 20:28:22.51338	f	\N	{"matches": 2, "runs": 346, "batting_avg": 34.6, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 23.29, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_248	2025-11-05 20:28:22.513525	2025-11-06 09:28:58.735509	\N	0.97	2025-11-05 21:31:58.188396	f
f7171413-6505-4e8b-b6e0-145b02a8232c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	SureshMyana	bowler	25	2025-11-05 20:28:22.849837	f	\N	{"matches": 1, "runs": 2, "batting_avg": 2.0, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 26.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_414	2025-11-05 20:28:22.85002	2025-11-06 09:28:58.735509	\N	4.83	2025-11-05 21:31:58.188401	f
f77f7841-d346-43e3-823e-2fbc2376282c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	WajidZulfiqar	all-rounder	25	2025-11-05 20:28:22.603823	f	\N	{"matches": 2, "runs": 200, "batting_avg": 28.57, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 17.29, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_398	2025-11-05 20:28:22.60398	2025-11-06 09:28:58.73551	\N	1.19	2025-11-05 21:31:58.188402	f
f79f5de8-5f43-4268-b6cd-eb9ac747997d	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	PriyathamKatukuri	batsman	25	2025-11-05 20:28:22.568354	f	\N	{"matches": 3, "runs": 361, "batting_avg": 36.1, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 34.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_444	2025-11-05 20:28:22.568498	2025-11-06 09:28:58.73551	\N	0.99	2025-11-05 21:31:58.188416	f
f845740c-5518-4b81-8c0a-ccbc2c41bc6a	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	ZuhaibRashid	all-rounder	25	2025-11-05 20:28:22.401327	f	\N	{"matches": 2, "runs": 445, "batting_avg": 23.42, "strike_rate": 0.0, "wickets": 16, "bowling_avg": 19.56, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_052	2025-11-05 20:28:22.401474	2025-11-06 09:28:58.73551	\N	0.93	2025-11-05 21:31:58.18842	f
f87ffe02-8f00-42ac-aa92-ed60afcbd63b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	AbhinavGill	batsman	25	2025-11-05 20:28:22.658513	f	\N	{"matches": 1, "runs": 208, "batting_avg": 26.0, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 51.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_540	2025-11-05 20:28:22.658667	2025-11-06 09:28:58.73551	\N	2.08	2025-11-05 21:31:58.188423	f
f8ce6f74-eb23-4da8-af06-472a81e1a71a	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	AlexanderWard	batsman	25	2025-11-05 20:28:22.794279	f	\N	{"matches": 1, "runs": 57, "batting_avg": 11.4, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 102.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_372	2025-11-05 20:28:22.794437	2025-11-06 09:28:58.73551	\N	4.14	2025-11-05 21:31:58.188426	f
f8fda0dd-df20-4a0a-a2bf-5e4229c544d1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	SrikanthSuryadevara	bowler	25	2025-11-05 20:28:22.717808	f	\N	{"matches": 2, "runs": 11, "batting_avg": 3.67, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 26.38, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_267	2025-11-05 20:28:22.717973	2025-11-06 09:28:58.735511	\N	3.35	2025-11-05 21:31:58.188428	f
f95a23ff-f597-4167-b954-01e4ba514b72	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	HenryDolphin	all-rounder	25	2025-11-05 20:28:22.735356	f	\N	{"matches": 1, "runs": 99, "batting_avg": 19.8, "strike_rate": 0.0, "wickets": 4, "bowling_avg": 36.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_206	2025-11-05 20:28:22.735514	2025-11-06 09:28:58.735511	\N	3.34	2025-11-05 21:31:58.188429	f
f98f9025-066d-4192-aa22-0408dc428c20	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	RahulSingh	batsman	25	2025-11-05 20:28:22.412119	f	\N	{"matches": 3, "runs": 663, "batting_avg": 28.83, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 61.33, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_023	2025-11-05 20:28:22.412272	2025-11-06 09:28:58.735511	\N	0.92	2025-11-05 21:31:58.188431	f
fb36a230-b4de-4c3b-abde-e53f08271183	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	EkagraArya	batsman	25	2025-11-05 20:28:22.810084	f	\N	{"matches": 1, "runs": 34, "batting_avg": 11.33, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 65.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_260	2025-11-05 20:28:22.810255	2025-11-06 09:28:58.735511	\N	4.37	2025-11-05 21:31:58.188483	f
fd77b989-4a41-46d3-b1bd-b78d8c74863c	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	ZuhaibKhaliq	bowler	25	2025-11-05 20:28:22.73255	f	\N	{"matches": 2, "runs": 19, "batting_avg": 3.8, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 44.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_656	2025-11-05 20:28:22.732694	2025-11-06 09:28:58.735512	\N	3.5	2025-11-05 21:31:58.188494	f
fd8a064f-828d-4480-8cf7-8f0005c41fac	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	AnshulSah	batsman	25	2025-11-05 20:28:22.718609	f	\N	{"matches": 2, "runs": 132, "batting_avg": 18.86, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 12.67, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_202	2025-11-05 20:28:22.71875	2025-11-06 09:28:58.735512	\N	3.02	2025-11-05 21:31:58.1885	f
fdc1ca7b-c1f7-4739-90ec-719a5b0d4276	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	AarushJanardhanan	all-rounder	25	2025-11-05 20:28:22.530455	f	\N	{"matches": 1, "runs": 384, "batting_avg": 20.21, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 13.33, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_167	2025-11-05 20:28:22.530601	2025-11-06 09:28:58.735512	\N	0.98	2025-11-05 21:31:58.188502	f
fe0a10d4-deba-4cf1-8db4-7f4df28924b2	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	MatsPrenen	all-rounder	25	2025-11-05 20:28:22.472752	f	\N	{"matches": 1, "runs": 439, "batting_avg": 36.58, "strike_rate": 0.0, "wickets": 6, "bowling_avg": 17.33, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_421	2025-11-05 20:28:22.472999	2025-11-06 09:28:58.735513	\N	0.96	2025-11-05 21:31:58.188505	f
fe436d8c-b5c7-4037-97b2-77862ce6d755	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	NiekRijnbeek	all-rounder	25	2025-11-05 20:28:22.421106	f	\N	{"matches": 2, "runs": 386, "batting_avg": 27.57, "strike_rate": 0.0, "wickets": 15, "bowling_avg": 27.67, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_049	2025-11-05 20:28:22.421254	2025-11-06 09:28:58.735513	\N	0.94	2025-11-05 21:31:58.188507	f
ff3477e4-cbde-41bc-87f9-d8e0204fa896	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	VinaySuresh	batsman	25	2025-11-05 20:28:22.761037	f	\N	{"matches": 2, "runs": 97, "batting_avg": 16.17, "strike_rate": 0.0, "wickets": 2, "bowling_avg": 88.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_048	2025-11-05 20:28:22.761179	2025-11-06 09:28:58.735513	\N	3.68	2025-11-05 21:31:58.188511	f
ff47b387-b943-4813-9c2c-56b35b85dd98	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	NaseerAhmed	all-rounder	25	2025-11-05 20:28:22.71045	f	\N	{"matches": 1, "runs": 54, "batting_avg": 27.0, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 46.14, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_635	2025-11-05 20:28:22.710596	2025-11-06 09:28:58.735513	\N	3.16	2025-11-05 21:31:58.188513	f
ff4e5782-4934-47f3-8cae-548848ba7f11	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	CasperDekeling	all-rounder	25	2025-11-05 20:28:22.493504	f	\N	{"matches": 2, "runs": 387, "batting_avg": 19.35, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 38.71, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_435	2025-11-05 20:28:22.493656	2025-11-06 09:28:58.735513	\N	0.97	2025-11-05 21:31:58.188515	f
fdcd492e-7285-46d1-a883-6cabb69f25bb	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	KhalidMughal	batsman	25	2025-11-05 20:28:22.329457	f	\N	{"matches": 12, "runs": 1099, "batting_avg": 68.69, "strike_rate": 0.0, "wickets": 17, "bowling_avg": 32.53, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_047	2025-11-05 20:28:22.329678	2025-11-06 10:09:45.313093	\N	0.8	2025-11-05 21:31:58.188504	t
5b33fcf3-7d30-4b2d-b203-9d24eb2d4c7e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	36b9f713-1009-459b-859c-26fa4a23c4d1	SiddharthGoyal	batsman	25	2025-11-05 20:28:22.436739	f	\N	{"matches": 9, "runs": 289, "batting_avg": 20.64, "strike_rate": 0.0, "wickets": 17, "bowling_avg": 41.76, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_040	2025-11-05 20:28:22.436918	2025-11-06 10:09:45.314522	\N	0.95	2025-11-05 21:31:58.18754	t
d3f48736-f1ae-440b-8fb6-ca60d9c16f92	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	ParagBawane	batsman	25	2025-11-05 20:28:22.361355	f	\N	{"matches": 1, "runs": 937, "batting_avg": 52.06, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 31.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_468	2025-11-05 20:28:22.361506	2025-11-06 10:09:45.315824	\N	0.88	2025-11-05 21:31:58.188231	t
d0f81038-7c87-4116-b3de-508c210b6559	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	eea4736e-3222-403b-ac06-f4484e3174c3	PiyushPandey	batsman	25	2025-11-05 20:28:22.362286	f	\N	{"matches": 10, "runs": 612, "batting_avg": 55.64, "strike_rate": 0.0, "wickets": 17, "bowling_avg": 20.12, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_245	2025-11-05 20:28:22.362438	2025-11-06 10:09:45.317116	\N	0.89	2025-11-05 21:31:58.188217	t
067991da-7190-470a-a08f-ddfa25ef36a5	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	SeanWalsh	batsman	25	2025-11-05 20:28:22.405728	f	\N	{"matches": 7, "runs": 690, "batting_avg": 49.29, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 26.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_123	2025-11-05 20:28:22.405881	2025-11-06 10:09:45.318583	\N	0.92	2025-11-05 21:31:58.187072	t
e5d7a119-5901-4832-adb4-7fac9e4690da	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	AyaanFarooq	batsman	25	2025-11-05 20:28:22.511582	f	\N	{"matches": 13, "runs": 328, "batting_avg": 21.87, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 39.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_020	2025-11-05 20:28:22.511727	2025-11-06 10:09:45.321153	\N	0.97	2025-11-05 21:31:58.188327	t
ee225874-6f0e-4fe2-9163-e692f05e5937	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	RakeshSripatnala	batsman	25	2025-11-05 20:28:22.351275	f	\N	{"matches": 14, "runs": 707, "batting_avg": 26.19, "strike_rate": 0.0, "wickets": 16, "bowling_avg": 32.5, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_114	2025-11-05 20:28:22.351426	2025-11-06 10:09:45.322299	\N	0.88	2025-11-05 21:31:58.18836	t
0e7b81aa-2f47-44e8-82e0-84b9ea58f8b3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	25f47fed-cad9-47ae-b8f3-4970af5d3b35	SohamPatel	batsman	25	2025-11-05 20:28:22.560368	f	\N	{"matches": 7, "runs": 221, "batting_avg": 27.63, "strike_rate": 0.0, "wickets": 9, "bowling_avg": 22.33, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_072	2025-11-05 20:28:22.56052	2025-11-06 10:09:45.323513	\N	0.99	2025-11-05 21:31:58.187114	t
02d08e45-b0be-47a4-b421-06ec39492262	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	RishiMohan	all-rounder	25	2025-11-05 20:28:22.649385	f	\N	{"matches": 1, "runs": 72, "batting_avg": 9.0, "strike_rate": 0.0, "wickets": 10, "bowling_avg": 47.7, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_289	2025-11-05 20:28:22.649528	2025-11-06 09:28:58.735397	\N	2.26	2025-11-05 21:31:58.187044	f
02d275c9-1b39-4bca-9f3a-0f71e0fbf41f	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	3cf39d67-48bf-4f7c-a535-7d9cb780997b	JoshuaKhawaja	bowler	25	2025-11-05 20:28:22.694144	f	\N	{"matches": 2, "runs": 45, "batting_avg": 11.25, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 21.88, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_452	2025-11-05 20:28:22.694304	2025-11-06 09:28:58.735397	\N	3.03	2025-11-05 21:31:58.187051	f
01022fb5-a396-495c-a680-63c172b2a840	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	ShreyashMehta	all-rounder	25	2025-11-05 20:28:22.370902	f	\N	{"matches": 1, "runs": 290, "batting_avg": 22.31, "strike_rate": 0.0, "wickets": 30, "bowling_avg": 16.3, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_528	2025-11-05 20:28:22.371072	2025-11-06 09:28:58.735392	\N	0.91	2025-11-05 21:31:58.188518	f
015e78ca-5800-429c-9dd3-351538bc62e1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	4dd5536e-a838-4bcf-9ddd-c7178894129a	KaranSeth	batsman	25	2025-11-05 20:28:22.743277	f	\N	{"matches": 7, "runs": 111, "batting_avg": 18.5, "strike_rate": 0.0, "wickets": 3, "bowling_avg": 22.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_064	2025-11-05 20:28:22.74343	2025-11-06 09:28:58.735394	\N	3.33	2025-11-05 21:31:58.188521	f
f87a9b05-97f0-41c6-82c5-f673fcf67fe5	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	b3aaa883-477d-452b-8be8-49d91b0bd993	AyaanBarve	all-rounder	25	2025-11-05 20:28:22.315588	f	\N	{"matches": 2, "runs": 465, "batting_avg": 21.14, "strike_rate": 0.0, "wickets": 91, "bowling_avg": 16.78, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_338	2025-11-05 20:28:22.316888	2025-11-05 21:31:58.30425	\N	0.69	2025-11-05 21:31:58.188421	f
fc56c88f-36c4-4ff7-9b98-42c1327a8cff	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ecb3b816-3837-41e1-a63c-9038caf15027	AreebShoaib	batsman	25	2025-11-05 20:28:22.67094	f	\N	{"matches": 2, "runs": 201, "batting_avg": 14.36, "strike_rate": 0.0, "wickets": 1, "bowling_avg": 45.0, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_003	2025-11-05 20:28:22.671085	2025-11-06 09:28:58.735511	\N	2.34	2025-11-05 21:31:58.188488	f
fc677fbf-5218-42fb-8320-8d6c4f1b8c2e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	AkashArora	batsman	25	2025-11-05 20:28:22.417332	f	\N	{"matches": 3, "runs": 574, "batting_avg": 21.26, "strike_rate": 0.0, "wickets": 7, "bowling_avg": 20.71, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_593	2025-11-05 20:28:22.417496	2025-11-06 09:28:58.735512	\N	0.93	2025-11-05 21:31:58.188489	f
fcce9f14-c835-4b93-b35d-480af2ecc11a	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	16a5038c-00a0-44b1-bc51-d3af67510d13	PulkitSaxena	bowler	25	2025-11-05 20:28:22.724271	f	\N	{"matches": 7, "runs": 4, "batting_avg": 1.0, "strike_rate": 0.0, "wickets": 8, "bowling_avg": 27.75, "economy": 0.0, "catches": 0, "run_outs": 0}	\N	\N	acc_legacy_089	2025-11-05 20:28:22.724414	2025-11-06 09:28:58.735512	\N	3.41	2025-11-05 21:31:58.188492	f
\.


--
-- Data for Name: seasons; Type: TABLE DATA; Schema: public; Owner: cricket_admin
--

COPY public.seasons (id, year, name, start_date, end_date, description, is_active, registration_open, scraping_enabled, created_at, updated_at, created_by) FROM stdin;
380f5bce-e6fc-4e75-947d-617fad9d5ee8	2026	Testing season 2026 	2026-04-01 00:00:00	2026-09-30 00:00:00	First season with admin system	t	t	t	2025-11-05 19:57:21.844883	2025-11-06 08:41:16.253817	68baefba-2fa8-4902-9e29-4a174600b880
\.


--
-- Data for Name: teams; Type: TABLE DATA; Schema: public; Owner: cricket_admin
--

COPY public.teams (id, club_id, name, level, tier_type, value_multiplier, points_multiplier, created_at, updated_at) FROM stdin;
dc3c0a4c-8892-4ce7-aed7-6f5f47ac620e	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ACC 1	1	senior	1	1	2025-11-05 20:15:52.923107	2025-11-05 20:15:52.923109
413865ef-caa0-467d-a1fe-e022abc360a0	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ACC 2	2	senior	1	1	2025-11-05 20:15:55.099003	2025-11-05 20:15:55.099012
ecb3b816-3837-41e1-a63c-9038caf15027	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ACC 3	3	senior	1	1	2025-11-05 20:15:57.086641	2025-11-05 20:15:57.086646
36b9f713-1009-459b-859c-26fa4a23c4d1	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ACC 4	4	senior	1	1	2025-11-05 20:15:59.32273	2025-11-05 20:15:59.322735
16a5038c-00a0-44b1-bc51-d3af67510d13	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ACC 5	5	senior	1	1	2025-11-05 20:16:01.550184	2025-11-05 20:16:01.550188
eea4736e-3222-403b-ac06-f4484e3174c3	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ACC 6	6	senior	1	1	2025-11-05 20:16:03.760145	2025-11-05 20:16:03.760149
4dd5536e-a838-4bcf-9ddd-c7178894129a	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	ZAMI 1	zami_1	senior	1	1	2025-11-05 20:16:06.277488	2025-11-05 20:16:06.27749
b3aaa883-477d-452b-8be8-49d91b0bd993	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	U17	u17	youth	1	1	2025-11-05 20:16:10.855675	2025-11-05 20:16:10.855678
3cf39d67-48bf-4f7c-a535-7d9cb780997b	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	U15	u15	youth	1	1	2025-11-05 20:16:13.306054	2025-11-05 20:16:13.306059
25f47fed-cad9-47ae-b8f3-4970af5d3b35	a7a580a7-7d3f-476c-82ea-afa6ae7ee276	U13	u13	youth	1	1	2025-11-05 20:16:15.605317	2025-11-05 20:16:15.605323
\.


--
-- Data for Name: transfers; Type: TABLE DATA; Schema: public; Owner: cricket_admin
--

COPY public.transfers (id, fantasy_team_id, player_out_id, player_in_id, transfer_type, requires_approval, is_approved, approved_by, proof_url, created_at, approved_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: cricket_admin
--

COPY public.users (id, email, password_hash, full_name, is_active, is_verified, is_admin, created_at, last_login) FROM stdin;
68baefba-2fa8-4902-9e29-4a174600b880	admin@fantcric.fun	$2b$12$Ik88IyZn7U5tvW0vo/aMi./qiTY6UCXnx8vRQTcsu.4cuCsFsKmp2	Admin User	t	t	t	2025-11-05 19:55:04.080736	2025-11-06 18:08:59.634031
82d5d8ef-6080-4e79-a48e-5a6383825d33	guy@leaf.cloud	$2b$12$X929g2RLqzlSno0SwgXPKeY7KHVVGuY7.LY74UGxNkIrUgot4Bo/W	Guy testeroso	t	f	f	2025-11-06 13:49:27.97415	2025-11-06 19:10:44.221462
\.


--
-- Name: clubs clubs_pkey; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.clubs
    ADD CONSTRAINT clubs_pkey PRIMARY KEY (id);


--
-- Name: fantasy_team_players fantasy_team_players_pkey; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.fantasy_team_players
    ADD CONSTRAINT fantasy_team_players_pkey PRIMARY KEY (id);


--
-- Name: fantasy_teams fantasy_teams_pkey; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.fantasy_teams
    ADD CONSTRAINT fantasy_teams_pkey PRIMARY KEY (id);


--
-- Name: leagues leagues_league_code_key; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.leagues
    ADD CONSTRAINT leagues_league_code_key UNIQUE (league_code);


--
-- Name: leagues leagues_pkey; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.leagues
    ADD CONSTRAINT leagues_pkey PRIMARY KEY (id);


--
-- Name: player_performances player_performances_pkey; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.player_performances
    ADD CONSTRAINT player_performances_pkey PRIMARY KEY (id);


--
-- Name: player_performances player_performances_player_id_league_id_round_number_key; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.player_performances
    ADD CONSTRAINT player_performances_player_id_league_id_round_number_key UNIQUE (player_id, league_id, round_number);


--
-- Name: player_price_history player_price_history_pkey; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.player_price_history
    ADD CONSTRAINT player_price_history_pkey PRIMARY KEY (id);


--
-- Name: players players_pkey; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT players_pkey PRIMARY KEY (id);


--
-- Name: seasons seasons_pkey; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.seasons
    ADD CONSTRAINT seasons_pkey PRIMARY KEY (id);


--
-- Name: seasons seasons_year_key; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.seasons
    ADD CONSTRAINT seasons_year_key UNIQUE (year);


--
-- Name: teams teams_pkey; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_pkey PRIMARY KEY (id);


--
-- Name: transfers transfers_pkey; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.transfers
    ADD CONSTRAINT transfers_pkey PRIMARY KEY (id);


--
-- Name: teams uq_club_team_level; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT uq_club_team_level UNIQUE (club_id, level);


--
-- Name: fantasy_teams uq_league_user; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.fantasy_teams
    ADD CONSTRAINT uq_league_user UNIQUE (league_id, user_id);


--
-- Name: clubs uq_season_club; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.clubs
    ADD CONSTRAINT uq_season_club UNIQUE (season_id, name);


--
-- Name: fantasy_team_players uq_team_player; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.fantasy_team_players
    ADD CONSTRAINT uq_team_player UNIQUE (fantasy_team_id, player_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_club_season; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_club_season ON public.clubs USING btree (season_id);


--
-- Name: idx_fantasy_team_league; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_fantasy_team_league ON public.fantasy_teams USING btree (league_id);


--
-- Name: idx_fantasy_team_user; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_fantasy_team_user ON public.fantasy_teams USING btree (user_id);


--
-- Name: idx_ftp_player; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_ftp_player ON public.fantasy_team_players USING btree (player_id);


--
-- Name: idx_ftp_team; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_ftp_team ON public.fantasy_team_players USING btree (fantasy_team_id);


--
-- Name: idx_league_club; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_league_club ON public.leagues USING btree (club_id);


--
-- Name: idx_league_code; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_league_code ON public.leagues USING btree (league_code);


--
-- Name: idx_league_season; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_league_season ON public.leagues USING btree (season_id);


--
-- Name: idx_perf_fantasy_team; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_perf_fantasy_team ON public.player_performances USING btree (fantasy_team_id);


--
-- Name: idx_perf_league; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_perf_league ON public.player_performances USING btree (league_id);


--
-- Name: idx_perf_league_round; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_perf_league_round ON public.player_performances USING btree (league_id, round_number);


--
-- Name: idx_perf_player; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_perf_player ON public.player_performances USING btree (player_id);


--
-- Name: idx_perf_round; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_perf_round ON public.player_performances USING btree (round_number);


--
-- Name: idx_player_club; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_player_club ON public.players USING btree (club_id);


--
-- Name: idx_player_legacy; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_player_legacy ON public.players USING btree (legacy_player_id);


--
-- Name: idx_player_team; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_player_team ON public.players USING btree (team_id);


--
-- Name: idx_player_value; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_player_value ON public.players USING btree (fantasy_value);


--
-- Name: idx_price_history_date; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_price_history_date ON public.player_price_history USING btree (changed_at);


--
-- Name: idx_price_history_player; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_price_history_player ON public.player_price_history USING btree (player_id);


--
-- Name: idx_team_club; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_team_club ON public.teams USING btree (club_id);


--
-- Name: idx_transfer_approval; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_transfer_approval ON public.transfers USING btree (requires_approval, is_approved);


--
-- Name: idx_transfer_team; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_transfer_team ON public.transfers USING btree (fantasy_team_id);


--
-- Name: idx_user_email; Type: INDEX; Schema: public; Owner: cricket_admin
--

CREATE INDEX idx_user_email ON public.users USING btree (email);


--
-- Name: clubs clubs_season_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.clubs
    ADD CONSTRAINT clubs_season_id_fkey FOREIGN KEY (season_id) REFERENCES public.seasons(id);


--
-- Name: fantasy_team_players fantasy_team_players_fantasy_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.fantasy_team_players
    ADD CONSTRAINT fantasy_team_players_fantasy_team_id_fkey FOREIGN KEY (fantasy_team_id) REFERENCES public.fantasy_teams(id);


--
-- Name: fantasy_team_players fantasy_team_players_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.fantasy_team_players
    ADD CONSTRAINT fantasy_team_players_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.players(id);


--
-- Name: fantasy_teams fantasy_teams_league_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.fantasy_teams
    ADD CONSTRAINT fantasy_teams_league_id_fkey FOREIGN KEY (league_id) REFERENCES public.leagues(id);


--
-- Name: leagues fk_leagues_club_id; Type: FK CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.leagues
    ADD CONSTRAINT fk_leagues_club_id FOREIGN KEY (club_id) REFERENCES public.clubs(id);


--
-- Name: leagues leagues_season_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.leagues
    ADD CONSTRAINT leagues_season_id_fkey FOREIGN KEY (season_id) REFERENCES public.seasons(id);


--
-- Name: player_performances player_performances_fantasy_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.player_performances
    ADD CONSTRAINT player_performances_fantasy_team_id_fkey FOREIGN KEY (fantasy_team_id) REFERENCES public.fantasy_teams(id);


--
-- Name: player_performances player_performances_league_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.player_performances
    ADD CONSTRAINT player_performances_league_id_fkey FOREIGN KEY (league_id) REFERENCES public.leagues(id);


--
-- Name: player_performances player_performances_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.player_performances
    ADD CONSTRAINT player_performances_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.players(id);


--
-- Name: player_price_history player_price_history_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.player_price_history
    ADD CONSTRAINT player_price_history_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.players(id);


--
-- Name: players players_club_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT players_club_id_fkey FOREIGN KEY (club_id) REFERENCES public.clubs(id);


--
-- Name: players players_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT players_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.teams(id);


--
-- Name: teams teams_club_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_club_id_fkey FOREIGN KEY (club_id) REFERENCES public.clubs(id);


--
-- Name: transfers transfers_fantasy_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.transfers
    ADD CONSTRAINT transfers_fantasy_team_id_fkey FOREIGN KEY (fantasy_team_id) REFERENCES public.fantasy_teams(id) ON DELETE CASCADE;


--
-- Name: transfers transfers_player_in_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.transfers
    ADD CONSTRAINT transfers_player_in_id_fkey FOREIGN KEY (player_in_id) REFERENCES public.players(id) ON DELETE CASCADE;


--
-- Name: transfers transfers_player_out_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cricket_admin
--

ALTER TABLE ONLY public.transfers
    ADD CONSTRAINT transfers_player_out_id_fkey FOREIGN KEY (player_out_id) REFERENCES public.players(id) ON DELETE SET NULL;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: cricket_admin
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

\unrestrict i6OrvhNYTQbM3CznkqszENi3ZXDcTHl5XwHSBlUDJfqnqubdtj9FXm9rdw7trxX

