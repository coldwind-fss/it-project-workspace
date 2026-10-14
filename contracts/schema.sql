--
-- PostgreSQL database dump
--


-- Dumped from database version 13.23
-- Dumped by pg_dump version 13.23

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
-- Name: json_array_length(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.json_array_length(value text) RETURNS integer
    LANGUAGE plpgsql IMMUTABLE
    AS $$
        BEGIN RETURN jsonb_array_length(value::jsonb); EXCEPTION WHEN others THEN RETURN 0; END;
        $$;


--
-- Name: json_valid(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.json_valid(value text) RETURNS boolean
    LANGUAGE plpgsql IMMUTABLE
    AS $$
        BEGIN PERFORM value::json; RETURN TRUE; EXCEPTION WHEN others THEN RETURN FALSE; END;
        $$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: app_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_logs (
    id text NOT NULL,
    level text DEFAULT 'error'::text,
    source text DEFAULT ''::text,
    message text DEFAULT ''::text,
    detail text DEFAULT ''::text,
    path text DEFAULT ''::text,
    useragent text DEFAULT ''::text,
    username text DEFAULT ''::text,
    createdat text DEFAULT ''::text
);


--
-- Name: app_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_sessions (
    token text NOT NULL,
    userid text NOT NULL,
    expiresat text NOT NULL,
    createdat text DEFAULT ''::text
);


--
-- Name: app_users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_users (
    id text NOT NULL,
    dinguserid text,
    name text,
    mobile text DEFAULT ''::text,
    avatar text DEFAULT ''::text,
    title text DEFAULT ''::text,
    department text DEFAULT ''::text,
    role text DEFAULT 'viewer'::text,
    devownername text DEFAULT ''::text,
    raw text DEFAULT '{}'::text,
    lastloginat text DEFAULT ''::text
);


--
-- Name: business_attachments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.business_attachments (
    id text NOT NULL,
    ownertype text NOT NULL,
    ownerid text NOT NULL,
    originalname text NOT NULL,
    storedname text NOT NULL,
    mimetype text DEFAULT 'application/octet-stream'::text,
    fileextension text DEFAULT ''::text,
    sizebytes bigint DEFAULT 0,
    sha256 text DEFAULT ''::text,
    storagekey text NOT NULL,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    deletedat text DEFAULT ''::text
);


--
-- Name: business_collaboration_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.business_collaboration_items (
    id text NOT NULL,
    requirementid text NOT NULL,
    businessrequestid text DEFAULT ''::text,
    direction text DEFAULT 'business_to_it'::text,
    kind text DEFAULT 'feedback'::text,
    status text DEFAULT 'open'::text,
    title text NOT NULL,
    content text DEFAULT ''::text,
    requesteruserid text DEFAULT ''::text,
    requestername text DEFAULT ''::text,
    recipientuserid text DEFAULT ''::text,
    recipientname text DEFAULT ''::text,
    duedate text DEFAULT ''::text,
    response text DEFAULT ''::text,
    sourcetype text DEFAULT 'in_app'::text,
    sourceref text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    respondedat text DEFAULT ''::text,
    closedat text DEFAULT ''::text
);


--
-- Name: business_collaboration_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.business_collaboration_messages (
    id text NOT NULL,
    collaborationid text NOT NULL,
    requirementid text NOT NULL,
    senderuserid text DEFAULT ''::text,
    sendername text DEFAULT ''::text,
    senderside text DEFAULT 'business'::text,
    messagetype text DEFAULT 'message'::text,
    content text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    deletedat text DEFAULT ''::text
);


--
-- Name: business_intake_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.business_intake_requests (
    id text NOT NULL,
    kind text NOT NULL,
    status text DEFAULT 'submitted'::text,
    title text NOT NULL,
    originalfeedback text DEFAULT ''::text,
    requesteruserid text DEFAULT ''::text,
    requestername text DEFAULT ''::text,
    department text DEFAULT ''::text,
    projectid text DEFAULT ''::text,
    projectname text DEFAULT ''::text,
    requirementid text DEFAULT ''::text,
    requirementtitle text DEFAULT ''::text,
    assignee text DEFAULT ''::text,
    assigneeuserid text DEFAULT ''::text,
    expecteddeliverytime text DEFAULT ''::text,
    priority text DEFAULT 'P2'::text,
    sourcetype text DEFAULT 'in_app'::text,
    sourceref text DEFAULT ''::text,
    handlernote text DEFAULT ''::text,
    handledbyuserid text DEFAULT ''::text,
    handledbyname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    handledat text DEFAULT ''::text,
    businessurgency text DEFAULT 'normal'::text
);


--
-- Name: categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.categories (
    id text NOT NULL,
    name text NOT NULL,
    icon text,
    description text,
    createdat text,
    owner text DEFAULT '[]'::text,
    sortorder bigint DEFAULT 0,
    color text DEFAULT '#3b82f6'::text,
    status text DEFAULT 'active'::text,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    deletedat text DEFAULT ''::text,
    deletedbyuserid text DEFAULT ''::text,
    deletedbyname text DEFAULT ''::text
);


--
-- Name: changelogs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.changelogs (
    id text NOT NULL,
    requirementid text,
    requirementtitle text,
    changetype text,
    fieldname text,
    oldvalue text,
    newvalue text,
    reason text,
    operator text,
    createdat text
);


--
-- Name: collaboration_link_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.collaboration_link_requests (
    id text NOT NULL,
    requirementid text NOT NULL,
    collaborationid text NOT NULL,
    requestmessageid text NOT NULL,
    kind text NOT NULL,
    token text NOT NULL,
    clientkey text NOT NULL,
    snapshot text NOT NULL,
    status text DEFAULT 'pending'::text,
    expiresat text NOT NULL,
    responsemessageid text DEFAULT ''::text,
    outcome text DEFAULT ''::text,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    createdat text NOT NULL,
    submittedat text DEFAULT ''::text,
    revokedat text DEFAULT ''::text
);


--
-- Name: demand_collection_batches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.demand_collection_batches (
    id text NOT NULL,
    notificationid text NOT NULL,
    targettype text DEFAULT ''::text,
    targetvalue text DEFAULT ''::text,
    targetlabel text DEFAULT ''::text,
    message text DEFAULT ''::text,
    status text DEFAULT 'sent'::text,
    recipientcount integer DEFAULT 0,
    successcount integer DEFAULT 0,
    failurecount integer DEFAULT 0,
    responsecount integer DEFAULT 0,
    pendingcount integer DEFAULT 0,
    valuablecount integer DEFAULT 0,
    excludedcount integer DEFAULT 0,
    sentbyuserid text DEFAULT ''::text,
    sentbyname text DEFAULT ''::text,
    sentat text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    requestkey text DEFAULT ''::text,
    runkey text DEFAULT ''::text,
    acceptedcount integer DEFAULT 0,
    unknowncount integer DEFAULT 0
);


--
-- Name: demand_collection_responses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.demand_collection_responses (
    id text NOT NULL,
    batchid text NOT NULL,
    notificationid text DEFAULT ''::text,
    recipienttoken text DEFAULT ''::text,
    recipientuserid text DEFAULT ''::text,
    recipientname text DEFAULT ''::text,
    recipientdepartment text DEFAULT ''::text,
    topickey text DEFAULT ''::text,
    topiclabel text DEFAULT ''::text,
    title text DEFAULT ''::text,
    problem text DEFAULT ''::text,
    frequency text DEFAULT ''::text,
    desired text DEFAULT ''::text,
    description text DEFAULT ''::text,
    department text DEFAULT ''::text,
    expecteddeliverytime text DEFAULT ''::text,
    businesspriority text DEFAULT 'normal'::text,
    intakelevel text DEFAULT 'L3'::text,
    responsedata text DEFAULT '{}'::text,
    judgment text DEFAULT 'pending'::text,
    judgmentreason text DEFAULT ''::text,
    similardemandid text DEFAULT ''::text,
    nextaction text DEFAULT ''::text,
    judgedbyuserid text DEFAULT ''::text,
    judgedbyname text DEFAULT ''::text,
    judgedat text DEFAULT ''::text,
    converteddemandid text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text
);


--
-- Name: demand_pool_confirmations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.demand_pool_confirmations (
    id text NOT NULL,
    demandid text NOT NULL,
    recipientuserid text DEFAULT ''::text,
    recipientname text DEFAULT ''::text,
    status text DEFAULT 'pending'::text,
    businessprocess text DEFAULT ''::text,
    usagescope text DEFAULT ''::text,
    usagefrequency text DEFAULT ''::text,
    acceptancecriteria text DEFAULT ''::text,
    successmetric text DEFAULT ''::text,
    confirmationcomment text DEFAULT ''::text,
    confirmedbyuserid text DEFAULT ''::text,
    confirmedbyname text DEFAULT ''::text,
    confirmedat text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    token text DEFAULT ''::text,
    notificationstatus text DEFAULT 'pending'::text,
    notificationerror text DEFAULT ''::text,
    sentat text DEFAULT ''::text,
    templatetype text DEFAULT 'custom'::text,
    content text DEFAULT '{}'::text
);


--
-- Name: demand_pool_delivery_units; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.demand_pool_delivery_units (
    id text NOT NULL,
    demandid text NOT NULL,
    sortorder integer DEFAULT 1,
    title text NOT NULL,
    scope text DEFAULT ''::text,
    acceptancedelta text DEFAULT ''::text,
    itemkind text DEFAULT 'feature'::text,
    valuemetrickeys text DEFAULT '[]'::text,
    requirementid text DEFAULT ''::text,
    status text DEFAULT 'draft'::text,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text
);


--
-- Name: demand_pool_evaluations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.demand_pool_evaluations (
    id text NOT NULL,
    demandid text NOT NULL,
    phase text DEFAULT 'triage'::text,
    solutiontype text DEFAULT ''::text,
    intakepath text DEFAULT ''::text,
    aimode text DEFAULT 'none'::text,
    aiscenario text DEFAULT ''::text,
    pocrequirement text DEFAULT 'none'::text,
    impactscope text DEFAULT 'single_department'::text,
    complexitylevel text DEFAULT 'medium'::text,
    completeness text DEFAULT 'complete'::text,
    similardemandid text DEFAULT ''::text,
    nextaction text DEFAULT ''::text,
    decision text DEFAULT ''::text,
    reason text DEFAULT ''::text,
    notes text DEFAULT ''::text,
    answers text DEFAULT '{}'::text,
    operatoruserid text DEFAULT ''::text,
    operatorname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text
);


--
-- Name: demand_pool_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.demand_pool_items (
    id text NOT NULL,
    title text NOT NULL,
    description text DEFAULT ''::text,
    requesteruserid text DEFAULT ''::text,
    requestername text DEFAULT ''::text,
    department text DEFAULT ''::text,
    projectid text DEFAULT ''::text,
    projectname text DEFAULT ''::text,
    expecteddeliverytime text DEFAULT ''::text,
    businesspriority text DEFAULT 'normal'::text,
    sourcetype text DEFAULT 'in_app'::text,
    sourceref text DEFAULT ''::text,
    status text DEFAULT 'pending_evaluation'::text,
    requesttype text DEFAULT ''::text,
    evaluationdecision text DEFAULT ''::text,
    evaluationreason text DEFAULT ''::text,
    evaluationnotes text DEFAULT ''::text,
    evaluationowneruserid text DEFAULT ''::text,
    evaluationownername text DEFAULT ''::text,
    evaluatedat text DEFAULT ''::text,
    confirmedat text DEFAULT ''::text,
    requirementid text DEFAULT ''::text,
    requirementtitle text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    closedat text DEFAULT ''::text,
    intakelevel text DEFAULT 'L3'::text,
    solutiontype text DEFAULT ''::text,
    intakepath text DEFAULT ''::text,
    aimode text DEFAULT 'none'::text,
    aiscenario text DEFAULT ''::text,
    pocrequirement text DEFAULT 'none'::text,
    impactscope text DEFAULT 'single_department'::text,
    complexitylevel text DEFAULT 'medium'::text,
    completeness text DEFAULT 'complete'::text,
    similardemandid text DEFAULT ''::text,
    nextaction text DEFAULT ''::text,
    deletedat text DEFAULT ''::text,
    deletedbyuserid text DEFAULT ''::text,
    deletedbyname text DEFAULT ''::text
);


--
-- Name: demand_pool_l3_branches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.demand_pool_l3_branches (
    id text NOT NULL,
    demandid text NOT NULL,
    sortorder integer DEFAULT 1,
    branchkey text NOT NULL,
    title text NOT NULL,
    itemkind text DEFAULT 'feature'::text,
    scope text DEFAULT ''::text,
    difference text DEFAULT ''::text,
    relationtovalue text DEFAULT 'shared'::text,
    proposedpriority text DEFAULT ''::text,
    dependency text DEFAULT ''::text,
    businessdecision text DEFAULT ''::text,
    businesspriority text DEFAULT ''::text,
    businesscomment text DEFAULT ''::text,
    itdecision text DEFAULT ''::text,
    itreason text DEFAULT ''::text,
    itnotes text DEFAULT ''::text,
    formalrequirementid text DEFAULT ''::text,
    status text DEFAULT 'draft'::text,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text
);


--
-- Name: demand_pool_link_notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.demand_pool_link_notifications (
    id text NOT NULL,
    targettype text DEFAULT 'person'::text,
    targetvalue text DEFAULT ''::text,
    targetlabel text DEFAULT ''::text,
    recipientuserids text DEFAULT '[]'::text,
    recipientnames text DEFAULT '[]'::text,
    message text DEFAULT ''::text,
    link text DEFAULT ''::text,
    sentbyuserid text DEFAULT ''::text,
    sentbyname text DEFAULT ''::text,
    status text DEFAULT 'pending'::text,
    successcount bigint DEFAULT 0,
    failurecount bigint DEFAULT 0,
    error text DEFAULT ''::text,
    sentat text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    entrymode text DEFAULT 'collect'::text,
    demandid text DEFAULT ''::text,
    schedulecycle text DEFAULT 'once'::text,
    scheduletime text DEFAULT ''::text,
    scheduleday bigint DEFAULT 0,
    enabled bigint DEFAULT 1,
    lastsentdate text DEFAULT ''::text,
    scheduleweekdays text DEFAULT '[1,2,3,4,5]'::text,
    requestkey text DEFAULT ''::text
);


--
-- Name: demand_pool_link_recipients; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.demand_pool_link_recipients (
    token text NOT NULL,
    notificationid text NOT NULL,
    recipientuserid text DEFAULT ''::text,
    recipientname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    usedat text DEFAULT ''::text,
    lastdemandid text DEFAULT ''::text,
    recipientdepartment text DEFAULT ''::text,
    entrymode text DEFAULT 'collect'::text,
    demandid text DEFAULT ''::text,
    batchid text DEFAULT ''::text,
    sendstatus text DEFAULT 'pending'::text,
    attemptcount integer DEFAULT 0,
    lastattemptat text DEFAULT ''::text,
    nextattemptat text DEFAULT ''::text,
    acceptedat text DEFAULT ''::text,
    errorcode text DEFAULT ''::text,
    errormessage text DEFAULT ''::text,
    providerrequestid text DEFAULT ''::text
);


--
-- Name: demand_pool_pocs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.demand_pool_pocs (
    id text NOT NULL,
    demandid text NOT NULL,
    status text DEFAULT 'draft'::text,
    goal text DEFAULT ''::text,
    baseline text DEFAULT ''::text,
    scope text DEFAULT ''::text,
    testdata text DEFAULT ''::text,
    successcriteria text DEFAULT ''::text,
    owneruserid text DEFAULT ''::text,
    ownername text DEFAULT ''::text,
    duedate text DEFAULT ''::text,
    result text DEFAULT ''::text,
    conclusion text DEFAULT ''::text,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    completedat text DEFAULT ''::text,
    artifacttype text DEFAULT 'text'::text,
    aiused text DEFAULT 'none'::text,
    ainotes text DEFAULT ''::text
);


--
-- Name: demand_pool_reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.demand_pool_reviews (
    id text NOT NULL,
    demandid text NOT NULL,
    reviewerrole text DEFAULT 'department_owner'::text,
    reviewerrolelabel text DEFAULT ''::text,
    revieweruserid text DEFAULT ''::text,
    reviewername text DEFAULT ''::text,
    reviewerdepartment text DEFAULT ''::text,
    status text DEFAULT 'pending'::text,
    decision text DEFAULT ''::text,
    valueassessment text DEFAULT ''::text,
    prioritysuggestion text DEFAULT ''::text,
    expectedoutcome text DEFAULT ''::text,
    risknotes text DEFAULT ''::text,
    comment text DEFAULT ''::text,
    link text DEFAULT ''::text,
    notificationstatus text DEFAULT ''::text,
    notificationerror text DEFAULT ''::text,
    sentat text DEFAULT ''::text,
    submittedat text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    token text DEFAULT ''::text,
    branchdecisions text DEFAULT '{}'::text
);


--
-- Name: demand_pool_supplements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.demand_pool_supplements (
    id text NOT NULL,
    demandid text NOT NULL,
    solutiontype text DEFAULT ''::text,
    status text DEFAULT 'pending'::text,
    questions text DEFAULT '[]'::text,
    answers text DEFAULT '{}'::text,
    recipientuserid text DEFAULT ''::text,
    recipientname text DEFAULT ''::text,
    submittedat text DEFAULT ''::text,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text
);


--
-- Name: demand_pool_value_cards; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.demand_pool_value_cards (
    id text NOT NULL,
    demandid text NOT NULL,
    status text DEFAULT 'draft'::text,
    baseline text DEFAULT '{}'::text,
    expected text DEFAULT '{}'::text,
    day7 text DEFAULT '{}'::text,
    day30 text DEFAULT '{}'::text,
    targetmet text DEFAULT ''::text,
    owneruserid text DEFAULT ''::text,
    ownername text DEFAULT ''::text,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    requirementid text DEFAULT ''::text,
    projectid text DEFAULT ''::text
);


--
-- Name: demand_pool_value_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.demand_pool_value_requests (
    id text NOT NULL,
    demandid text NOT NULL,
    stage text DEFAULT 'goal'::text NOT NULL,
    token text NOT NULL,
    recipientuserid text DEFAULT ''::text,
    recipientname text DEFAULT ''::text,
    status text DEFAULT 'pending'::text,
    scheduledat text DEFAULT ''::text,
    notificationstatus text DEFAULT ''::text,
    notificationerror text DEFAULT ''::text,
    sentat text DEFAULT ''::text,
    submittedat text DEFAULT ''::text,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    requirementid text DEFAULT ''::text,
    projectid text DEFAULT ''::text,
    responsesnapshot text DEFAULT '{}'::text,
    viewedat text DEFAULT ''::text
);


--
-- Name: dingtalk_card_deliveries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dingtalk_card_deliveries (
    id text NOT NULL,
    outtrackid text NOT NULL,
    targetid text DEFAULT ''::text,
    scopetype text DEFAULT ''::text,
    scopeid text DEFAULT ''::text,
    activityid text DEFAULT ''::text,
    eventtype text DEFAULT ''::text,
    recipientuserid text DEFAULT ''::text,
    conversationid text DEFAULT ''::text,
    cardinstanceid text DEFAULT ''::text,
    status text DEFAULT 'delivered'::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text
);


--
-- Name: dingtalk_card_interactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dingtalk_card_interactions (
    id text NOT NULL,
    outtrackid text NOT NULL,
    action text NOT NULL,
    userid text DEFAULT ''::text,
    username text DEFAULT ''::text,
    activityid text DEFAULT ''::text,
    createdat text DEFAULT ''::text
);


--
-- Name: improvement_proposals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.improvement_proposals (
    id text NOT NULL,
    operationid text DEFAULT ''::text,
    requirementid text DEFAULT ''::text,
    projectid text DEFAULT ''::text,
    sourcetype text DEFAULT 'manual'::text,
    sourceid text DEFAULT ''::text,
    title text NOT NULL,
    problem text DEFAULT ''::text,
    suggestion text DEFAULT ''::text,
    expectedchange text DEFAULT ''::text,
    status text DEFAULT '待评估'::text,
    linkedrequirementid text DEFAULT ''::text,
    owneruserid text DEFAULT ''::text,
    ownername text DEFAULT ''::text,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    adoptedat text DEFAULT ''::text
);


--
-- Name: notification_delivery_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notification_delivery_logs (
    id text NOT NULL,
    targetid text DEFAULT ''::text,
    targetname text DEFAULT ''::text,
    triggertype text DEFAULT 'manual'::text,
    eventtype text DEFAULT ''::text,
    dedupekey text DEFAULT ''::text,
    status text DEFAULT 'success'::text,
    error text DEFAULT ''::text,
    sentat text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text
);


--
-- Name: notification_targets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notification_targets (
    id text NOT NULL,
    name text NOT NULL,
    webhook text NOT NULL,
    secret text DEFAULT ''::text,
    scope text DEFAULT 'dashboard'::text,
    developer text DEFAULT ''::text,
    contenttypes text DEFAULT '["activities","changelogs"]'::text,
    enabled bigint DEFAULT 1,
    scheduletime text DEFAULT ''::text,
    lastsentdate text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    customcontent text DEFAULT ''::text,
    developeruserid text DEFAULT ''::text,
    owneruserid text DEFAULT ''::text,
    ownername text DEFAULT ''::text,
    schedulecycle text DEFAULT 'daily'::text,
    scheduleday bigint DEFAULT 0,
    contentrange text DEFAULT 'today'::text,
    customrangestart text DEFAULT ''::text,
    customrangeend text DEFAULT ''::text,
    deliverychannel text DEFAULT 'group'::text,
    recipientname text DEFAULT ''::text,
    recipientuserid text DEFAULT ''::text,
    targettype text DEFAULT 'global'::text,
    projectid text DEFAULT ''::text,
    requirementid text DEFAULT ''::text,
    triggertype text DEFAULT 'schedule'::text,
    triggerevents text DEFAULT '[]'::text,
    lastsentat text DEFAULT ''::text,
    lastsendstatus text DEFAULT ''::text,
    lastsenderror text DEFAULT ''::text,
    scheduleweekdays text DEFAULT '[1,2,3,4,5]'::text,
    cardtargettype text DEFAULT 'personal'::text,
    cardconversationid text DEFAULT ''::text,
    cardtemplateid text DEFAULT ''::text,
    cardrobotcode text DEFAULT ''::text,
    reportscene text DEFAULT 'daily'::text
);


--
-- Name: operation_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.operation_records (
    id text NOT NULL,
    entitytype text,
    entityid text,
    entityname text,
    action text,
    operator text DEFAULT ''::text,
    operatorrole text DEFAULT ''::text,
    summary text DEFAULT ''::text,
    beforevalue text DEFAULT '{}'::text,
    aftervalue text DEFAULT '{}'::text,
    createdat text DEFAULT ''::text,
    sourcebatchid text DEFAULT ''::text
);


--
-- Name: performance_months; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.performance_months (
    id text NOT NULL,
    userid text NOT NULL,
    month text NOT NULL,
    goals text DEFAULT ''::text,
    plan text DEFAULT ''::text,
    nextplan text DEFAULT ''::text,
    draft text DEFAULT '{}'::text,
    finaltext text DEFAULT ''::text,
    status text DEFAULT 'draft'::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    finalizedat text DEFAULT ''::text
);


--
-- Name: pm_migration_meta; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pm_migration_meta (
    key text NOT NULL,
    value text NOT NULL
);


--
-- Name: poc_workbench_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.poc_workbench_records (
    id text NOT NULL,
    recordtype text DEFAULT 'poc'::text,
    title text NOT NULL,
    status text DEFAULT 'draft'::text,
    conclusion text DEFAULT ''::text,
    owneruserid text DEFAULT ''::text,
    ownername text DEFAULT ''::text,
    projectid text DEFAULT ''::text,
    projectname text DEFAULT ''::text,
    requirementid text DEFAULT ''::text,
    requirementtitle text DEFAULT ''::text,
    demandid text DEFAULT ''::text,
    demandtitle text DEFAULT ''::text,
    sourcetype text DEFAULT 'manual'::text,
    sourceref text DEFAULT ''::text,
    derivedfromid text DEFAULT ''::text,
    objective text DEFAULT ''::text,
    hypothesis text DEFAULT ''::text,
    scope text DEFAULT ''::text,
    sampledata text DEFAULT ''::text,
    method text DEFAULT ''::text,
    successcriteria text DEFAULT ''::text,
    result text DEFAULT ''::text,
    limitations text DEFAULT ''::text,
    nextsteps text DEFAULT ''::text,
    modelname text DEFAULT ''::text,
    modelversion text DEFAULT ''::text,
    promptorapproach text DEFAULT ''::text,
    metrics text DEFAULT '{}'::text,
    reuseguidance text DEFAULT ''::text,
    tags text DEFAULT '[]'::text,
    artifacttype text DEFAULT 'text'::text,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    completedat text DEFAULT ''::text,
    archivedat text DEFAULT ''::text
);


--
-- Name: postlaunch_issues; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.postlaunch_issues (
    id text NOT NULL,
    operationid text DEFAULT ''::text,
    requirementid text DEFAULT ''::text,
    projectid text DEFAULT ''::text,
    sourcetype text DEFAULT 'manual'::text,
    sourceid text DEFAULT ''::text,
    title text NOT NULL,
    description text DEFAULT ''::text,
    severity text DEFAULT '一般'::text,
    status text DEFAULT '待核实'::text,
    owneruserid text DEFAULT ''::text,
    ownername text DEFAULT ''::text,
    duedate text DEFAULT ''::text,
    resolution text DEFAULT ''::text,
    rootcause text DEFAULT ''::text,
    prevention text DEFAULT ''::text,
    discoveredat text DEFAULT ''::text,
    firstresponseat text DEFAULT ''::text,
    resolvedat text DEFAULT ''::text,
    reopenedcount bigint DEFAULT 0,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    closedat text DEFAULT ''::text
);


--
-- Name: postlaunch_knowledge; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.postlaunch_knowledge (
    id text NOT NULL,
    operationid text DEFAULT ''::text,
    requirementid text DEFAULT ''::text,
    projectid text DEFAULT ''::text,
    title text NOT NULL,
    content text DEFAULT ''::text,
    artifacttype text DEFAULT 'text'::text,
    sourcetype text DEFAULT 'postlaunch'::text,
    sourceid text DEFAULT ''::text,
    status text DEFAULT 'draft'::text,
    owneruserid text DEFAULT ''::text,
    ownername text DEFAULT ''::text,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    publishedat text DEFAULT ''::text
);


--
-- Name: postlaunch_operations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.postlaunch_operations (
    id text NOT NULL,
    requirementid text DEFAULT ''::text,
    projectid text DEFAULT ''::text,
    demandid text DEFAULT ''::text,
    deliverykind text DEFAULT '上线'::text,
    deliverydate text DEFAULT ''::text,
    usestartdate text DEFAULT ''::text,
    businessowneruserid text DEFAULT ''::text,
    businessownername text DEFAULT ''::text,
    status text DEFAULT 'active'::text,
    day7duedate text DEFAULT ''::text,
    day30duedate text DEFAULT ''::text,
    day7requestid text DEFAULT ''::text,
    day30requestid text DEFAULT ''::text,
    notes text DEFAULT ''::text,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    deliveryroundid text DEFAULT ''::text,
    acceptancerequestid text DEFAULT ''::text,
    acceptancesnapshot text DEFAULT '{}'::text,
    verificationexemption text DEFAULT ''::text,
    planneddeliverydate text DEFAULT ''::text
);


--
-- Name: projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.projects (
    id text NOT NULL,
    name text NOT NULL,
    description text,
    status text DEFAULT 'active'::text,
    priority text DEFAULT 'P2'::text,
    department text DEFAULT ''::text,
    businessowner text DEFAULT ''::text,
    devowner text DEFAULT ''::text,
    currentversion text DEFAULT 'v1.0.0'::text,
    startdate text DEFAULT ''::text,
    targetenddate text DEFAULT ''::text,
    categoryid text DEFAULT ''::text,
    images text DEFAULT '[]'::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    deletedat text DEFAULT ''::text,
    deletedbyuserid text DEFAULT ''::text,
    deletedbyname text DEFAULT ''::text,
    solutiontype text DEFAULT 'unknown'::text,
    lifecycletemplate text DEFAULT ''::text,
    complexitylevel text DEFAULT 'medium'::text
);


--
-- Name: releases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.releases (
    id text NOT NULL,
    projectid text,
    version text,
    releasedate text,
    summary text,
    type text
);


--
-- Name: requirement_delivery_baselines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.requirement_delivery_baselines (
    id text NOT NULL,
    requirementid text NOT NULL,
    version bigint DEFAULT 1 NOT NULL,
    templatetype text DEFAULT ''::text,
    content text DEFAULT '{}'::text NOT NULL,
    status text DEFAULT 'draft'::text NOT NULL,
    recipientuserid text DEFAULT ''::text,
    recipientname text DEFAULT ''::text,
    confirmationlinkid text DEFAULT ''::text,
    supersedesid text DEFAULT ''::text,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    confirmedat text DEFAULT ''::text,
    sourcedemandconfirmationid text DEFAULT ''::text
);


--
-- Name: requirement_delivery_feedback; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.requirement_delivery_feedback (
    id text NOT NULL,
    requirementid text NOT NULL,
    deliveryroundid text NOT NULL,
    baselineid text DEFAULT ''::text,
    feedbacktype text DEFAULT 'other'::text NOT NULL,
    routetype text DEFAULT 'it_review'::text NOT NULL,
    content text DEFAULT ''::text,
    requestedtitle text DEFAULT ''::text,
    routedrequirementid text DEFAULT ''::text,
    status text DEFAULT 'pending'::text NOT NULL,
    submittedbyuserid text DEFAULT ''::text,
    submittedbyname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    resolvedat text DEFAULT ''::text
);


--
-- Name: requirement_phase_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.requirement_phase_templates (
    id text NOT NULL,
    solutiontype text NOT NULL,
    phasekey text NOT NULL,
    phaselabel text NOT NULL,
    description text DEFAULT ''::text,
    required bigint DEFAULT 0,
    sortorder bigint DEFAULT 0,
    enabled bigint DEFAULT 1,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text
);


--
-- Name: requirement_phases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.requirement_phases (
    id text NOT NULL,
    requirementid text NOT NULL,
    phasekey text NOT NULL,
    phaselabel text NOT NULL,
    description text DEFAULT ''::text,
    status text DEFAULT 'todo'::text,
    owneruserid text DEFAULT ''::text,
    ownername text DEFAULT ''::text,
    required bigint DEFAULT 0,
    sortorder bigint DEFAULT 0,
    plannedat text DEFAULT ''::text,
    startedat text DEFAULT ''::text,
    completedat text DEFAULT ''::text,
    evidence text DEFAULT '{}'::text,
    note text DEFAULT ''::text,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text
);


--
-- Name: requirement_work_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.requirement_work_logs (
    id text NOT NULL,
    requirementid text NOT NULL,
    logtype text DEFAULT '工作进展'::text,
    content text NOT NULL,
    operatoruserid text DEFAULT ''::text,
    operatorname text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    occurredat text DEFAULT ''::text,
    sourcebatchid text DEFAULT ''::text,
    workdate text DEFAULT ''::text,
    visibility text DEFAULT 'it_private'::text,
    sourcetype text DEFAULT 'manual'::text,
    sourceref text DEFAULT ''::text,
    reportingeligible integer DEFAULT 0,
    updatedat text DEFAULT ''::text
);


--
-- Name: requirements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.requirements (
    id text NOT NULL,
    title text NOT NULL,
    type text,
    priority text,
    status text,
    projectid text,
    projectname text,
    sprintid text,
    assignee text,
    requester text,
    description text,
    acceptancecriteria text DEFAULT ''::text,
    storypoints bigint DEFAULT 0,
    labels text DEFAULT ''::text,
    images text DEFAULT '[]'::text,
    createdat text,
    updatedat text,
    expecteddeliverytime text DEFAULT ''::text,
    department text DEFAULT ''::text,
    createdbyuserid text DEFAULT ''::text,
    createdbyname text DEFAULT ''::text,
    completedat text DEFAULT ''::text,
    deletedat text DEFAULT ''::text,
    deletedbyuserid text DEFAULT ''::text,
    deletedbyname text DEFAULT ''::text,
    priorityevaluation text DEFAULT '{}'::text,
    changeobject text DEFAULT ''::text,
    impactlevel text DEFAULT ''::text,
    workloadlevel text DEFAULT ''::text,
    itemkind text DEFAULT 'feature'::text,
    parentrequirementid text DEFAULT ''::text,
    versiontarget text DEFAULT ''::text,
    demandid text DEFAULT ''::text,
    flowmode text DEFAULT 'legacy'::text,
    lifecycleversion integer DEFAULT 1,
    reportingeligible integer DEFAULT 0,
    registeredat text DEFAULT ''::text,
    relatedrequirementid text DEFAULT ''::text
);


--
-- Name: shared_activities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shared_activities (
    id text NOT NULL,
    scopetype text DEFAULT 'requirement'::text NOT NULL,
    scopeid text NOT NULL,
    projectid text DEFAULT ''::text,
    requirementid text DEFAULT ''::text,
    activitytype text DEFAULT 'work_progress'::text,
    title text DEFAULT ''::text,
    content text DEFAULT ''::text,
    actoruserid text DEFAULT ''::text,
    actorname text DEFAULT ''::text,
    sourcetype text DEFAULT ''::text,
    sourceid text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    deletedat text DEFAULT ''::text
);


--
-- Name: shared_activity_comments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shared_activity_comments (
    id text NOT NULL,
    activityid text NOT NULL,
    projectid text DEFAULT ''::text,
    requirementid text DEFAULT ''::text,
    commenteruserid text DEFAULT ''::text,
    commentername text DEFAULT ''::text,
    content text DEFAULT ''::text,
    sourcetype text DEFAULT ''::text,
    sourceid text DEFAULT ''::text,
    createdat text DEFAULT ''::text,
    updatedat text DEFAULT ''::text,
    deletedat text DEFAULT ''::text
);


--
-- Name: sprints; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sprints (
    id text NOT NULL,
    name text NOT NULL,
    projectid text,
    startdate text,
    enddate text,
    status text,
    releasenotes text,
    totaltasks bigint,
    completedtasks bigint
);


--
-- Name: system_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.system_settings (
    key text NOT NULL,
    value text DEFAULT '{}'::text,
    updatedat text DEFAULT ''::text
);


--
-- Name: todos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.todos (
    id text NOT NULL,
    recipientuserid text DEFAULT ''::text,
    recipientname text DEFAULT ''::text,
    requirementid text DEFAULT ''::text,
    requirementtitle text DEFAULT ''::text,
    projectid text DEFAULT ''::text,
    projectname text DEFAULT ''::text,
    sourceuserid text DEFAULT ''::text,
    sourcename text DEFAULT ''::text,
    type text DEFAULT 'requirement_assigned'::text,
    status text DEFAULT 'unread'::text,
    message text DEFAULT ''::text,
    dingtalksent bigint DEFAULT 0,
    createdat text DEFAULT ''::text,
    readat text DEFAULT ''::text,
    doneat text DEFAULT ''::text,
    dingtalktaskid text DEFAULT ''::text,
    dingtalkunionid text DEFAULT ''::text,
    dingtalkerror text DEFAULT ''::text,
    businesscollaborationid text DEFAULT ''::text
);


--
-- Name: work_sync_batches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.work_sync_batches (
    id text NOT NULL,
    idempotencykey text NOT NULL,
    sourcetype text DEFAULT ''::text,
    sourceref text DEFAULT ''::text,
    sourcerangestart text DEFAULT ''::text,
    sourcerangeend text DEFAULT ''::text,
    projectid text NOT NULL,
    projectname text DEFAULT ''::text,
    operatoruserid text DEFAULT ''::text,
    operatorname text DEFAULT ''::text,
    payloadhash text DEFAULT ''::text,
    status text DEFAULT 'committed'::text,
    result text DEFAULT '{}'::text,
    createdat text DEFAULT ''::text,
    completedat text DEFAULT ''::text,
    rolledbackat text DEFAULT ''::text
);


--
-- Name: work_sync_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.work_sync_items (
    id text NOT NULL,
    batchid text NOT NULL,
    itemindex bigint DEFAULT 0,
    action text DEFAULT ''::text,
    recordkind text DEFAULT ''::text,
    requirementid text DEFAULT ''::text,
    title text DEFAULT ''::text,
    payload text DEFAULT '{}'::text,
    createdat text DEFAULT ''::text
);


--
-- Name: app_logs app_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_logs
    ADD CONSTRAINT app_logs_pkey PRIMARY KEY (id);


--
-- Name: app_sessions app_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_sessions
    ADD CONSTRAINT app_sessions_pkey PRIMARY KEY (token);


--
-- Name: app_users app_users_dinguserid_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_users
    ADD CONSTRAINT app_users_dinguserid_key UNIQUE (dinguserid);


--
-- Name: app_users app_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_users
    ADD CONSTRAINT app_users_pkey PRIMARY KEY (id);


--
-- Name: business_attachments business_attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_attachments
    ADD CONSTRAINT business_attachments_pkey PRIMARY KEY (id);


--
-- Name: business_collaboration_items business_collaboration_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_collaboration_items
    ADD CONSTRAINT business_collaboration_items_pkey PRIMARY KEY (id);


--
-- Name: business_collaboration_messages business_collaboration_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_collaboration_messages
    ADD CONSTRAINT business_collaboration_messages_pkey PRIMARY KEY (id);


--
-- Name: business_intake_requests business_intake_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_intake_requests
    ADD CONSTRAINT business_intake_requests_pkey PRIMARY KEY (id);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: changelogs changelogs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.changelogs
    ADD CONSTRAINT changelogs_pkey PRIMARY KEY (id);


--
-- Name: collaboration_link_requests collaboration_link_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.collaboration_link_requests
    ADD CONSTRAINT collaboration_link_requests_pkey PRIMARY KEY (id);


--
-- Name: collaboration_link_requests collaboration_link_requests_requirementid_clientkey_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.collaboration_link_requests
    ADD CONSTRAINT collaboration_link_requests_requirementid_clientkey_key UNIQUE (requirementid, clientkey);


--
-- Name: collaboration_link_requests collaboration_link_requests_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.collaboration_link_requests
    ADD CONSTRAINT collaboration_link_requests_token_key UNIQUE (token);


--
-- Name: demand_collection_batches demand_collection_batches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.demand_collection_batches
    ADD CONSTRAINT demand_collection_batches_pkey PRIMARY KEY (id);


--
-- Name: demand_collection_responses demand_collection_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.demand_collection_responses
    ADD CONSTRAINT demand_collection_responses_pkey PRIMARY KEY (id);


--
-- Name: demand_collection_responses demand_collection_responses_recipienttoken_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.demand_collection_responses
    ADD CONSTRAINT demand_collection_responses_recipienttoken_key UNIQUE (recipienttoken);


--
-- Name: demand_pool_confirmations demand_pool_confirmations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.demand_pool_confirmations
    ADD CONSTRAINT demand_pool_confirmations_pkey PRIMARY KEY (id);


--
-- Name: demand_pool_delivery_units demand_pool_delivery_units_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.demand_pool_delivery_units
    ADD CONSTRAINT demand_pool_delivery_units_pkey PRIMARY KEY (id);


--
-- Name: demand_pool_evaluations demand_pool_evaluations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.demand_pool_evaluations
    ADD CONSTRAINT demand_pool_evaluations_pkey PRIMARY KEY (id);


--
-- Name: demand_pool_items demand_pool_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.demand_pool_items
    ADD CONSTRAINT demand_pool_items_pkey PRIMARY KEY (id);


--
-- Name: demand_pool_l3_branches demand_pool_l3_branches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.demand_pool_l3_branches
    ADD CONSTRAINT demand_pool_l3_branches_pkey PRIMARY KEY (id);


--
-- Name: demand_pool_link_notifications demand_pool_link_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.demand_pool_link_notifications
    ADD CONSTRAINT demand_pool_link_notifications_pkey PRIMARY KEY (id);


--
-- Name: demand_pool_link_recipients demand_pool_link_recipients_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.demand_pool_link_recipients
    ADD CONSTRAINT demand_pool_link_recipients_pkey PRIMARY KEY (token);


--
-- Name: demand_pool_pocs demand_pool_pocs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.demand_pool_pocs
    ADD CONSTRAINT demand_pool_pocs_pkey PRIMARY KEY (id);


--
-- Name: demand_pool_reviews demand_pool_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.demand_pool_reviews
    ADD CONSTRAINT demand_pool_reviews_pkey PRIMARY KEY (id);


--
-- Name: demand_pool_supplements demand_pool_supplements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.demand_pool_supplements
    ADD CONSTRAINT demand_pool_supplements_pkey PRIMARY KEY (id);


--
-- Name: demand_pool_value_cards demand_pool_value_cards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.demand_pool_value_cards
    ADD CONSTRAINT demand_pool_value_cards_pkey PRIMARY KEY (id);


--
-- Name: demand_pool_value_requests demand_pool_value_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.demand_pool_value_requests
    ADD CONSTRAINT demand_pool_value_requests_pkey PRIMARY KEY (id);


--
-- Name: demand_pool_value_requests demand_pool_value_requests_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.demand_pool_value_requests
    ADD CONSTRAINT demand_pool_value_requests_token_key UNIQUE (token);


--
-- Name: dingtalk_card_deliveries dingtalk_card_deliveries_outtrackid_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dingtalk_card_deliveries
    ADD CONSTRAINT dingtalk_card_deliveries_outtrackid_key UNIQUE (outtrackid);


--
-- Name: dingtalk_card_deliveries dingtalk_card_deliveries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dingtalk_card_deliveries
    ADD CONSTRAINT dingtalk_card_deliveries_pkey PRIMARY KEY (id);


--
-- Name: dingtalk_card_interactions dingtalk_card_interactions_outtrackid_action_userid_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dingtalk_card_interactions
    ADD CONSTRAINT dingtalk_card_interactions_outtrackid_action_userid_key UNIQUE (outtrackid, action, userid);


--
-- Name: dingtalk_card_interactions dingtalk_card_interactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dingtalk_card_interactions
    ADD CONSTRAINT dingtalk_card_interactions_pkey PRIMARY KEY (id);


--
-- Name: improvement_proposals improvement_proposals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.improvement_proposals
    ADD CONSTRAINT improvement_proposals_pkey PRIMARY KEY (id);


--
-- Name: notification_delivery_logs notification_delivery_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_delivery_logs
    ADD CONSTRAINT notification_delivery_logs_pkey PRIMARY KEY (id);


--
-- Name: notification_targets notification_targets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_targets
    ADD CONSTRAINT notification_targets_pkey PRIMARY KEY (id);


--
-- Name: operation_records operation_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.operation_records
    ADD CONSTRAINT operation_records_pkey PRIMARY KEY (id);


--
-- Name: performance_months performance_months_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_months
    ADD CONSTRAINT performance_months_pkey PRIMARY KEY (id);


--
-- Name: performance_months performance_months_userid_month_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_months
    ADD CONSTRAINT performance_months_userid_month_key UNIQUE (userid, month);


--
-- Name: pm_migration_meta pm_migration_meta_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pm_migration_meta
    ADD CONSTRAINT pm_migration_meta_pkey PRIMARY KEY (key);


--
-- Name: poc_workbench_records poc_workbench_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.poc_workbench_records
    ADD CONSTRAINT poc_workbench_records_pkey PRIMARY KEY (id);


--
-- Name: postlaunch_issues postlaunch_issues_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.postlaunch_issues
    ADD CONSTRAINT postlaunch_issues_pkey PRIMARY KEY (id);


--
-- Name: postlaunch_knowledge postlaunch_knowledge_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.postlaunch_knowledge
    ADD CONSTRAINT postlaunch_knowledge_pkey PRIMARY KEY (id);


--
-- Name: postlaunch_operations postlaunch_operations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.postlaunch_operations
    ADD CONSTRAINT postlaunch_operations_pkey PRIMARY KEY (id);


--
-- Name: postlaunch_operations postlaunch_operations_requirementid_projectid_deliverydate__key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.postlaunch_operations
    ADD CONSTRAINT postlaunch_operations_requirementid_projectid_deliverydate__key UNIQUE (requirementid, projectid, deliverydate, deliveryroundid);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: releases releases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.releases
    ADD CONSTRAINT releases_pkey PRIMARY KEY (id);


--
-- Name: requirement_delivery_baselines requirement_delivery_baselines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.requirement_delivery_baselines
    ADD CONSTRAINT requirement_delivery_baselines_pkey PRIMARY KEY (id);


--
-- Name: requirement_delivery_feedback requirement_delivery_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.requirement_delivery_feedback
    ADD CONSTRAINT requirement_delivery_feedback_pkey PRIMARY KEY (id);


--
-- Name: requirement_phase_templates requirement_phase_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.requirement_phase_templates
    ADD CONSTRAINT requirement_phase_templates_pkey PRIMARY KEY (id);


--
-- Name: requirement_phases requirement_phases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.requirement_phases
    ADD CONSTRAINT requirement_phases_pkey PRIMARY KEY (id);


--
-- Name: requirement_phases requirement_phases_requirementid_phasekey_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.requirement_phases
    ADD CONSTRAINT requirement_phases_requirementid_phasekey_key UNIQUE (requirementid, phasekey);


--
-- Name: requirement_work_logs requirement_work_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.requirement_work_logs
    ADD CONSTRAINT requirement_work_logs_pkey PRIMARY KEY (id);


--
-- Name: requirements requirements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.requirements
    ADD CONSTRAINT requirements_pkey PRIMARY KEY (id);


--
-- Name: shared_activities shared_activities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shared_activities
    ADD CONSTRAINT shared_activities_pkey PRIMARY KEY (id);


--
-- Name: shared_activity_comments shared_activity_comments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shared_activity_comments
    ADD CONSTRAINT shared_activity_comments_pkey PRIMARY KEY (id);


--
-- Name: sprints sprints_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sprints
    ADD CONSTRAINT sprints_pkey PRIMARY KEY (id);


--
-- Name: system_settings system_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_pkey PRIMARY KEY (key);


--
-- Name: todos todos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.todos
    ADD CONSTRAINT todos_pkey PRIMARY KEY (id);


--
-- Name: work_sync_batches work_sync_batches_idempotencykey_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_sync_batches
    ADD CONSTRAINT work_sync_batches_idempotencykey_key UNIQUE (idempotencykey);


--
-- Name: work_sync_batches work_sync_batches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_sync_batches
    ADD CONSTRAINT work_sync_batches_pkey PRIMARY KEY (id);


--
-- Name: work_sync_items work_sync_items_batchid_itemindex_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_sync_items
    ADD CONSTRAINT work_sync_items_batchid_itemindex_key UNIQUE (batchid, itemindex);


--
-- Name: work_sync_items work_sync_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_sync_items
    ADD CONSTRAINT work_sync_items_pkey PRIMARY KEY (id);


--
-- Name: idx_business_attachments_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_business_attachments_owner ON public.business_attachments USING btree (ownertype, ownerid, createdat);


--
-- Name: idx_business_collab_messages_requirement; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_business_collab_messages_requirement ON public.business_collaboration_messages USING btree (requirementid, createdat);


--
-- Name: idx_business_collab_messages_thread; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_business_collab_messages_thread ON public.business_collaboration_messages USING btree (collaborationid, createdat);


--
-- Name: idx_business_collab_recipient; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_business_collab_recipient ON public.business_collaboration_items USING btree (recipientuserid, createdat);


--
-- Name: idx_business_collab_requirement; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_business_collab_requirement ON public.business_collaboration_items USING btree (requirementid, createdat);


--
-- Name: idx_business_intake_assignee; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_business_intake_assignee ON public.business_intake_requests USING btree (assigneeuserid, createdat);


--
-- Name: idx_business_intake_requester; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_business_intake_requester ON public.business_intake_requests USING btree (requesteruserid, createdat);


--
-- Name: idx_business_intake_requirement; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_business_intake_requirement ON public.business_intake_requests USING btree (requirementid, createdat);


--
-- Name: idx_collaboration_links_requirement; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_collaboration_links_requirement ON public.collaboration_link_requests USING btree (requirementid, createdat);


--
-- Name: idx_demand_collection_batches_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_collection_batches_created ON public.demand_collection_batches USING btree (createdat DESC);


--
-- Name: idx_demand_collection_batches_notification; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_collection_batches_notification ON public.demand_collection_batches USING btree (notificationid, createdat DESC);


--
-- Name: idx_demand_collection_responses_batch; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_collection_responses_batch ON public.demand_collection_responses USING btree (batchid, createdat DESC);


--
-- Name: idx_demand_collection_responses_judgment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_collection_responses_judgment ON public.demand_collection_responses USING btree (judgment, createdat DESC);


--
-- Name: idx_demand_pool_confirmations_demand; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_confirmations_demand ON public.demand_pool_confirmations USING btree (demandid, createdat);


--
-- Name: idx_demand_pool_confirmations_recipient; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_confirmations_recipient ON public.demand_pool_confirmations USING btree (recipientuserid, createdat);


--
-- Name: idx_demand_pool_confirmations_token; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_demand_pool_confirmations_token ON public.demand_pool_confirmations USING btree (token) WHERE (token <> ''::text);


--
-- Name: idx_demand_pool_delivery_units_demand; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_delivery_units_demand ON public.demand_pool_delivery_units USING btree (demandid, sortorder, createdat);


--
-- Name: idx_demand_pool_delivery_units_requirement; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_delivery_units_requirement ON public.demand_pool_delivery_units USING btree (requirementid);


--
-- Name: idx_demand_pool_department; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_department ON public.demand_pool_items USING btree (department, createdat);


--
-- Name: idx_demand_pool_evaluations_demand; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_evaluations_demand ON public.demand_pool_evaluations USING btree (demandid, createdat);


--
-- Name: idx_demand_pool_l3_branches_demand; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_l3_branches_demand ON public.demand_pool_l3_branches USING btree (demandid, sortorder, createdat);


--
-- Name: idx_demand_pool_link_notifications_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_link_notifications_created ON public.demand_pool_link_notifications USING btree (createdat);


--
-- Name: idx_demand_pool_link_recipients_batch_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_link_recipients_batch_status ON public.demand_pool_link_recipients USING btree (batchid, sendstatus, createdat DESC);


--
-- Name: idx_demand_pool_link_recipients_notification; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_link_recipients_notification ON public.demand_pool_link_recipients USING btree (notificationid, createdat);


--
-- Name: idx_demand_pool_pocs_demand; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_pocs_demand ON public.demand_pool_pocs USING btree (demandid, createdat);


--
-- Name: idx_demand_pool_requester; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_requester ON public.demand_pool_items USING btree (requesteruserid, createdat);


--
-- Name: idx_demand_pool_reviews_demand; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_reviews_demand ON public.demand_pool_reviews USING btree (demandid, createdat);


--
-- Name: idx_demand_pool_reviews_reviewer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_reviews_reviewer ON public.demand_pool_reviews USING btree (revieweruserid, status, createdat);


--
-- Name: idx_demand_pool_reviews_token; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_demand_pool_reviews_token ON public.demand_pool_reviews USING btree (token) WHERE (token <> ''::text);


--
-- Name: idx_demand_pool_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_status ON public.demand_pool_items USING btree (status, createdat);


--
-- Name: idx_demand_pool_supplements_demand; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_supplements_demand ON public.demand_pool_supplements USING btree (demandid, createdat);


--
-- Name: idx_demand_pool_value_cards_demand; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_value_cards_demand ON public.demand_pool_value_cards USING btree (demandid, createdat);


--
-- Name: idx_demand_pool_value_cards_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_value_cards_project ON public.demand_pool_value_cards USING btree (projectid, createdat);


--
-- Name: idx_demand_pool_value_cards_requirement; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_value_cards_requirement ON public.demand_pool_value_cards USING btree (requirementid, createdat);


--
-- Name: idx_demand_pool_value_requests_demand; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_value_requests_demand ON public.demand_pool_value_requests USING btree (demandid, stage, createdat);


--
-- Name: idx_demand_pool_value_requests_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_value_requests_project ON public.demand_pool_value_requests USING btree (projectid, stage, createdat);


--
-- Name: idx_demand_pool_value_requests_requirement; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_value_requests_requirement ON public.demand_pool_value_requests USING btree (requirementid, stage, createdat);


--
-- Name: idx_demand_pool_value_requests_schedule; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_demand_pool_value_requests_schedule ON public.demand_pool_value_requests USING btree (status, scheduledat);


--
-- Name: idx_improvement_proposals_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_improvement_proposals_status ON public.improvement_proposals USING btree (status, createdat);


--
-- Name: idx_notification_delivery_logs_dedupe; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notification_delivery_logs_dedupe ON public.notification_delivery_logs USING btree (targetid, dedupekey, status);


--
-- Name: idx_notification_delivery_logs_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notification_delivery_logs_target ON public.notification_delivery_logs USING btree (targetid, createdat DESC);


--
-- Name: idx_operation_records_source_batch; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_operation_records_source_batch ON public.operation_records USING btree (sourcebatchid);


--
-- Name: idx_performance_months_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_performance_months_user ON public.performance_months USING btree (userid, month);


--
-- Name: idx_poc_workbench_records_demand; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_poc_workbench_records_demand ON public.poc_workbench_records USING btree (demandid, updatedat DESC);


--
-- Name: idx_poc_workbench_records_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_poc_workbench_records_project ON public.poc_workbench_records USING btree (projectid, updatedat DESC);


--
-- Name: idx_poc_workbench_records_requirement; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_poc_workbench_records_requirement ON public.poc_workbench_records USING btree (requirementid, updatedat DESC);


--
-- Name: idx_poc_workbench_records_type_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_poc_workbench_records_type_status ON public.poc_workbench_records USING btree (recordtype, status, updatedat DESC);


--
-- Name: idx_postlaunch_issues_operation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_postlaunch_issues_operation ON public.postlaunch_issues USING btree (operationid, createdat);


--
-- Name: idx_postlaunch_issues_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_postlaunch_issues_status ON public.postlaunch_issues USING btree (status, severity, updatedat);


--
-- Name: idx_postlaunch_knowledge_operation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_postlaunch_knowledge_operation ON public.postlaunch_knowledge USING btree (operationid, createdat);


--
-- Name: idx_postlaunch_operations_due; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_postlaunch_operations_due ON public.postlaunch_operations USING btree (status, day7duedate, day30duedate);


--
-- Name: idx_postlaunch_operations_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_postlaunch_operations_project ON public.postlaunch_operations USING btree (projectid, createdat);


--
-- Name: idx_postlaunch_operations_requirement; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_postlaunch_operations_requirement ON public.postlaunch_operations USING btree (requirementid, createdat);


--
-- Name: idx_projects_category_deleted; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_category_deleted ON public.projects USING btree (categoryid, deletedat);


--
-- Name: idx_requirement_delivery_baseline_requirement; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_requirement_delivery_baseline_requirement ON public.requirement_delivery_baselines USING btree (requirementid, version, createdat);


--
-- Name: idx_requirement_delivery_feedback_requirement; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_requirement_delivery_feedback_requirement ON public.requirement_delivery_feedback USING btree (requirementid, createdat);


--
-- Name: idx_requirement_delivery_feedback_route; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_requirement_delivery_feedback_route ON public.requirement_delivery_feedback USING btree (routetype, status, createdat);


--
-- Name: idx_requirement_phases_requirement; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_requirement_phases_requirement ON public.requirement_phases USING btree (requirementid, sortorder, createdat);


--
-- Name: idx_requirement_work_logs_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_requirement_work_logs_created ON public.requirement_work_logs USING btree (createdat);


--
-- Name: idx_requirement_work_logs_reporting; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_requirement_work_logs_reporting ON public.requirement_work_logs USING btree (reportingeligible, workdate, createdat DESC);


--
-- Name: idx_requirement_work_logs_requirement; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_requirement_work_logs_requirement ON public.requirement_work_logs USING btree (requirementid, createdat);


--
-- Name: idx_requirement_work_logs_source_batch; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_requirement_work_logs_source_batch ON public.requirement_work_logs USING btree (sourcebatchid);


--
-- Name: idx_requirements_deleted_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_requirements_deleted_created ON public.requirements USING btree (deletedat, createdat);


--
-- Name: idx_requirements_demand; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_requirements_demand ON public.requirements USING btree (demandid, createdat DESC);


--
-- Name: idx_requirements_project_deleted; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_requirements_project_deleted ON public.requirements USING btree (projectid, deletedat);


--
-- Name: idx_requirements_reporting; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_requirements_reporting ON public.requirements USING btree (reportingeligible, status, updatedat DESC);


--
-- Name: idx_shared_activities_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shared_activities_created ON public.shared_activities USING btree (createdat);


--
-- Name: idx_shared_activities_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shared_activities_project ON public.shared_activities USING btree (projectid, createdat);


--
-- Name: idx_shared_activities_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shared_activities_scope ON public.shared_activities USING btree (scopetype, scopeid, createdat);


--
-- Name: idx_shared_activity_comments_activity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shared_activity_comments_activity ON public.shared_activity_comments USING btree (activityid, createdat);


--
-- Name: idx_work_sync_items_batch; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_work_sync_items_batch ON public.work_sync_items USING btree (batchid, itemindex);


--
-- Name: idx_work_sync_items_requirement; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_work_sync_items_requirement ON public.work_sync_items USING btree (requirementid);


--
-- Name: uq_demand_collection_batch_run; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_demand_collection_batch_run ON public.demand_collection_batches USING btree (runkey) WHERE (runkey <> ''::text);


--
-- Name: uq_demand_pool_l3_branch_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_demand_pool_l3_branch_key ON public.demand_pool_l3_branches USING btree (demandid, branchkey);


--
-- Name: uq_demand_pool_link_notification_request; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_demand_pool_link_notification_request ON public.demand_pool_link_notifications USING btree (requestkey) WHERE (requestkey <> ''::text);


--
-- Name: uq_postlaunch_delivery_round; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_postlaunch_delivery_round ON public.postlaunch_operations USING btree (requirementid, projectid, deliveryroundid) WHERE (deliveryroundid <> ''::text);


--
-- Name: uq_requirement_delivery_baseline_version; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_requirement_delivery_baseline_version ON public.requirement_delivery_baselines USING btree (requirementid, version);


--
-- Name: uq_requirement_delivery_feedback_round; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_requirement_delivery_feedback_round ON public.requirement_delivery_feedback USING btree (deliveryroundid);


--
-- Name: uq_requirement_phase_template; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_requirement_phase_template ON public.requirement_phase_templates USING btree (solutiontype, phasekey);


--
-- Name: uq_shared_activities_source; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_shared_activities_source ON public.shared_activities USING btree (sourcetype, sourceid);


--
-- Name: uq_shared_activity_comments_source; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_shared_activity_comments_source ON public.shared_activity_comments USING btree (sourcetype, sourceid);


--
-- PostgreSQL database dump complete
--
