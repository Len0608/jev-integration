# Integration Examples Reference

The following production-grade Stonebranch Universal Extension templates are provided as reference. Use them to guide field naming, type selection, credential design, and action structure.

## Field Type Reference

| Type       | When to use |
|------------|-------------|
| Choice     | Fixed enumeration — action modes, providers, protocols, regions |
| Credential | UAC Credential record reference — never store secrets inline |
| Text       | Free-form string — URLs, resource names, IDs, query strings |
| Script     | Multi-line editor — SQL, JSON payloads, shell snippets, prompts |
| Boolean    | Toggle flags — SSL verify, verbose logging, dry-run, wait mode |
| Integer    | Whole numbers — timeouts (s), retry counts, page sizes, ports |
| Float      | Decimal numbers — LLM temperature, top-p, penalty weights |
| Array      | Repeating key/value pairs — HTTP headers, env vars, parameters |

Design rules:
- Use one Credential field per authentication context (source vs. destination).
- Name credential fields clearly: `api_credential`, `sftp_credential`.
- Prefer Choice over Text for any field with a known fixed set of values.
- Use Integer for all numeric tuning knobs (timeout, retries, page size).
- Use Script only for multi-line content (payloads, queries, inline code).
- Output/status fields (Text) let operators capture results as UAC variables.

---

## Most Relevant Examples

### Web Service Integration — `ue-webservice`
**Category:** Web Services / REST
**Description:** Web Service Integration Universal Extension
**Fields (38):**

| Field name | Type | Choices / Notes |
|------------|------|-----------------|
| `protocol` | Choice | HTTP(S)/REST |
| `http_version` | Choice | 1.1 |
| `authorization_type` | Choice | Basic, Token, API Key, None, OAuth 2.0 |
| `credentials` | Credential |  |
| `api_key` | Credential |  |
| `access_token_url` | Text |  |
| `grant_type` | Choice | Client Credentials, Password Credentials |
| `scope` | Text |  |
| `client_credentials` | Credential |  |
| `resource_owner_credentials` | Credential |  |
| `client_authentication` | Choice | Send Client Credentials in Body, Send as Basic Auth Header |
| `oauth2_token` | Text |  |
| `add_authorization_data_to` | Choice | Request Header, Request URL |
| `authorization_header_prefix` | Text | Bearer |
| `additional_credentials` | Credential |  |
| `use_ssl` | Boolean | false |
| `ssl_hostname_check` | Boolean | true |
| `trusted_certificates_file` | Text |  |
| `private_key_certificate` | Text |  |
| `public_key_certificate` | Text |  |
| `http_method` | Choice | GET, POST, PUT, PATCH, DELETE |
| `timeout` | Float |  |
| `url` | Text |  |
| `url_query_parameters` | Array |  |
| `http_headers` | Array |  |
| `payload_type` | Choice | Raw, Form Data |
| `payload_source` | Choice | Form, Script |
| `payload_script` | Script |  |
| `mime_type` | Choice | application/javascript , application/json, application/xml, text/html, text/plain, text/xml |
| `other_value_for_mime_type` | Text |  |
| `form_data` | Array |  |
| `payload` | Text |  |
| `proxies` | Text |  |
| `result_body_medium` | Choice | --None--, STDOUT |
| `process_exit_code_mapping` | Boolean | false |
| `path_expression` | Text |  |
| `exit_code_mapping` | Array |  |
| `response_code` | Text |  |


### Kong AI Gateway — `ue-kong-ai-gateway`
**Category:** AI / API Gateway
**Description:** LLM chat and autonomous agentic MCP-tool automation via Kong AI Gateway.
**Fields (47):**

| Field name | Type | Choices / Notes |
|------------|------|-----------------|
| `action` | Choice | Chat, Agentic MCP, List MCP Tools |
| `auth_method` | Choice | OAuth2 (Client Credentials), Kong API Key (key-auth) |
| `credential` | Credential |  |
| `api_key_header_name` | Text | apikey |
| `kong_gateway_url` | Text |  |
| `activate_dynamic_choices` | Boolean | false |
| `activate_overrides` | Boolean | false |
| `kong_admin_api_url` | Text |  |
| `kong_admin_api_token` | Credential |  |
| `llm_service` | Choice |  |
| `model` | Choice |  |
| `mcp_connections` | Choice |  |
| `mcp_connections_override` | Text |  |
| `allowed_tools` | Choice |  |
| `allowed_tools_override` | Text |  |
| `system_prompt_source` | Choice | Inline Text, UAC Script |
| `system_prompt_text` | Text | You are a helpful assistant. |
| `system_prompt_script` | Script |  |
| `user_prompt_source` | Choice | Inline Text, UAC Script |
| `user_prompt_text` | Text |  |
| `user_prompt_script` | Script |  |
| `response_format_type` | Choice | Text, JSON (Prompt Described), JSON Schema (API Enforced) |
| `response_format_schema` | Script |  |
| `advanced_options` | Boolean | false |
| `temperature` | Float | 1.0 |
| `top_p` | Float | 1.0 |
| `frequency_penalty` | Float | 0.0 |
| `presence_penalty` | Float | 0.0 |
| `max_tokens` | Integer | 1000 |
| `seed` | Integer |  |
| `stop_sequences` | Text |  |
| `max_turns` | Integer | 20 |
| `poll_interval` | Integer | 5 |
| `dry_run` | Boolean | false |
| `save_options` | Choice | -- None --, Save Latest Response / Final Answer, Save Entire Conversation |
| `save_destination` | Text |  |
| `chat_stdout_options` | Choice | Latest Response Only, Entire Conversation |
| `agentic_stdout_options` | Choice | Final Answer Only, Loop Progress + Final Answer |
| `chat_output_options` | Choice | Token Usage and Metadata, Complete Conversation |
| `agentic_output_options` | Choice | Token Usage and Metadata, Tool-Call Transcript |
| `prompt_tokens` | Integer |  |
| `completion_tokens` | Integer |  |
| `total_tokens` | Integer |  |
| `finish_reason` | Text |  |
| `turns_used` | Integer |  |
| `tool_call_count` | Integer |  |
| `tool_count` | Integer |  |


### Apache Kafka: Event Monitor — `ue-kafka-monitor`
**Category:** Messaging / Event Streaming
**Description:** Apache Kafka: Event Monitor
**Fields (34):**

| Field name | Type | Choices / Notes |
|------------|------|-----------------|
| `action` | Choice | Monitor for events |
| `security_protocol` | Choice | PLAINTEXT, SASL_SSL, SSL |
| `bootstrap_servers` | Text |  |
| `sasl_mechanism` | Choice | SCRAM-SHA-512, SCRAM-SHA-256 |
| `ssl_cafile` | Text |  |
| `client_certificate_path` | Text |  |
| `sasl_user_credentials` | Credential |  |
| `client_private_key_path` | Text |  |
| `client_private_key_password` | Credential |  |
| `ssl_check_hostname` | Boolean | true |
| `topic` | Choice |  |
| `topic_sasl` | Choice |  |
| `topic_ssl` | Choice |  |
| `consumer_type` | Choice | Consumer Group |
| `consumer_group` | Text |  |
| `start_from` | Choice | Consumer Group Offset |
| `client_id` | Text |  |
| `key_deserializer` | Choice | Integer, String |
| `value_deserializer` | Choice | Integer, Float, String, JSON |
| `value_filter_number` | Choice | -- None --, >=, <=, =, != |
| `value_filter_string` | Choice | -- None --, Contains, Does Not Contain, Equals, Is Blank, Is Not Blank |
| `value_filter_json` | Choice | -- None --, >=, <=, =, !=, Contains |
| `value_number` | Text |  |
| `value_string` | Text |  |
| `value_json` | Text |  |
| `show_advanced_settings` | Boolean | false |
| `value_json_path` | Text |  |
| `partition_assign_strategy` | Choice | Range, Round Robin |
| `session_timeout_ms` | Integer | 10000 |
| `auto_offset_reset` | Choice | Latest, Earliest |
| `request_timeout_ms` | Integer | 305000 |
| `max_partition_fetch_bytes` | Integer | 1048576 |
| `heartbeat_interval_ms` | Integer | 3000 |
| `ops_task_id` | Text | ${ops_task_id} |

