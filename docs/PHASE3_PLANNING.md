# Phase 3: OpenTelemetry Distributed Observability

**Objective:** Add distributed tracing, performance metrics, and request flow visualization

## Components to Build

### 1. OpenTelemetry Setup (observability/tracing.py)
- Initialize OpenTelemetry SDK
- Configure OTLP exporter (Jaeger collector)
- Set up tracer provider
- Enable auto-instrumentation

### 2. Instrumentation Layer (observability/instrumentation.py)
- Span decorators for functions
- Async span context management
- W3C TraceContext propagation
- Baggage for metadata (org_id, user_id)

### 3. Tool Instrumentation
- Spans for each tool call
- Attributes: tool name, arguments, result, duration
- Events for checkpoints
- Links for parent-child relationships

### 4. Auth Instrumentation
- Spans for auth operations
- Attributes: method, endpoint, success/failure
- Links to tool execution spans

### 5. Docker Integration (observability/metrics.py)
- Container resource metrics
- CPU and memory usage per container
- Network I/O metrics
- Custom metrics for tool execution

### 6. Jaeger Deployment
- docker-compose service for Jaeger
- OTLP receiver configuration
- Trace storage (in-memory for dev, Elasticsearch for prod)
- UI on http://localhost:16686

## File Structure

```
src/observability/
  __init__.py
  tracing.py (150 lines)
    - initialize_tracer()
    - get_tracer()
    - configure_otlp_exporter()
    - set_up_instrumentation()
    
  instrumentation.py (200 lines)
    - trace_span decorator
    - trace_async_span decorator
    - set_baggage() context manager
    - extract_trace_context()
    - inject_trace_context()
    
  metrics.py (150 lines)
    - MetricsCollector class
    - collect_container_metrics()
    - record_tool_execution()
    - record_auth_event()
    
  handlers.py (100 lines)
    - add_trace_context_headers()
    - parse_trace_context_headers()
    - propagate_trace_context()
```

## Integration Points

1. **ASGI Middleware**
   - CorrelationMiddleware → inject W3C TraceContext
   - Extract trace context from headers
   - Pass to all downstream operations

2. **Tool Execution**
   - Span for tool call start
   - Span for docker container execution
   - Span for tool completion
   - Attributes: tool name, scopes, exit code, duration

3. **Auth Operations**
   - Span for token validation
   - Span for scope checking
   - Attributes: subject, org_id, scopes, result

4. **Database Operations**
   - Span for queries (if using DB)
   - Attributes: query type, table, duration

## W3C TraceContext Format

```
traceparent: 00-{trace-id}-{span-id}-{flags}
tracestate: {vendor}={value}

Example:
traceparent: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01
tracestate: digifortex=org_id:tenant123,user:user@example.com
```

## Jaeger Deployment

Docker Compose service:
```yaml
jaeger:
  image: jaegertracing/all-in-one:latest
  ports:
    - "6831:6831/udp"  # Jaeger agent
    - "16686:16686"    # UI
  environment:
    - COLLECTOR_OTLP_ENABLED=true
```

## Span Naming Convention

- `asgi.request` - HTTP request entry
- `auth.validate_token` - Token validation
- `auth.check_scope` - Scope check
- `tool.execute` - Tool execution
- `sandbox.run_command` - Container execution
- `sandbox.create_container` - Docker container creation
- `sandbox.cleanup_container` - Container cleanup

## Attributes Per Span

### asgi.request
- http.method
- http.url
- http.status_code
- http.client_ip
- http.user_agent

### auth.validate_token
- auth.token_type
- auth.subject
- auth.org_id
- auth.scopes
- auth.success

### auth.check_scope
- auth.required_scope
- auth.granted
- auth.subject
- auth.org_id

### tool.execute
- tool.name
- tool.scope_required
- tool.exit_code
- tool.stdout_length
- tool.stderr_length
- tool.duration_ms

### sandbox.run_command
- sandbox.command_hash
- sandbox.timeout
- sandbox.exit_code
- sandbox.cpu_used
- sandbox.memory_used

## Events in Spans

- `auth.success` - successful authentication
- `auth.failure` - failed authentication
- `scope.denied` - scope check failed
- `tool.started` - tool execution started
- `tool.completed` - tool execution completed
- `container.created` - Docker container created
- `container.destroyed` - Docker container cleaned up

## Metrics to Collect

### Counters
- auth_success_total
- auth_failure_total
- scope_check_total
- tool_execution_total
- container_creation_total

### Histograms
- auth_validation_duration_ms
- token_verification_duration_ms
- tool_execution_duration_ms
- container_startup_duration_ms
- container_cleanup_duration_ms

### Gauges
- active_containers
- active_spans
- active_requests

## Sample Trace View

In Jaeger UI, a single request would show:

```
POST /api/v1/mcp/tools/call (asgi.request)
├── auth.validate_token (JWT HS256 verification)
├── auth.check_scope (tools:shell:execute required)
├── tool.execute (run_command)
│   ├── sandbox.create_container
│   ├── sandbox.run_command
│   │   └── docker container execution
│   └── sandbox.cleanup_container
└── audit.log_event (tool execution logged)

Total: ~1-2s (cold container start), ~0.5s (warm)
```

## Implementation Order

1. Create observability/tracing.py (OpenTel setup)
2. Create observability/instrumentation.py (decorators)
3. Create observability/metrics.py (metrics)
4. Update asgi_app_with_sandbox.py (add middleware)
5. Instrument tool execution
6. Instrument auth operations
7. Add Jaeger to docker-compose
8. Create trace visualization dashboard
9. Test and verify traces in Jaeger UI

## Expected Outcome

✓ Every request has a trace ID and span hierarchy
✓ Tool execution timings visible
✓ Auth events correlated with tool calls
✓ Container metrics visible
✓ Jaeger UI shows full request flow
✓ Latency bottlenecks identified
✓ Error rates and failures tracked

