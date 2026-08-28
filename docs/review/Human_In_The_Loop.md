# AIDA Human In The Loop

**Document:** Book 2, Chapter 5 — Human In The Loop
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

Human-in-the-Loop (HITL) enables human oversight and intervention in autonomous workflows. It allows humans to approve, reject, pause, resume, edit plans, and provide instructions at critical decision points.

---

## 2. HITL Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HUMAN IN THE LOOP                                 │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Approval Manager                           │   │
│  │  - Request approval                                           │   │
│  │  - Track approval status                                      │   │
│  │  - Handle timeouts                                            │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│     ↓                       │                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Notification Manager                       │   │
│  │  - Send notifications                                         │   │
│  │  - Track delivery                                             │   │
│  │  - Handle responses                                           │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│     ↓                       │                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Response Handler                           │   │
│  │  - Process human response                                     │   │
│  │  - Execute decision                                           │   │
│  │  - Update workflow                                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. HITL Operations

### 3.1 Operation Types

| Operation | Description | Use Case |
|-----------|-------------|----------|
| `approve` | Approve step/workflow | Sensitive operations |
| `reject` | Reject step/workflow | Wrong approach |
| `pause` | Pause execution | Need to think |
| `resume` | Resume execution | Ready to continue |
| `edit_plan` | Modify execution plan | Better approach |
| `add_instructions` | Add new instructions | Additional context |
| `override` | Override AI decision | Human expertise |
| `cancel` | Cancel workflow | No longer needed |

---

## 4. Approval Flow

### 4.1 Approval Request

```python
class ApprovalRequest:
    request_id: UUID
    workflow_id: UUID
    step_id: Optional[str]
    
    # Request details
    request_type: str  # approve, reject, pause, etc.
    title: str
    description: str
    
    # Context
    current_state: dict
    proposed_action: dict
    alternatives: list[dict]
    
    # AI reasoning
    ai_reasoning: str
    ai_confidence: float
    
    # Timing
    created_at: datetime
    expires_at: Optional[datetime]
    
    # Status
    status: str  # pending, approved, rejected, timeout
    response: Optional[dict]
    responded_at: Optional[datetime]
```

### 4.2 Approval Process

```
Approval Required
    │
    ├── Create approval request
    │
    ├── Send notification to human
    │   ├── Email
    │   ├── Slack
    │   ├── WebSocket
    │   └── In-app notification
    │
    ├── Wait for response
    │   ├── Approved → Execute action
    │   ├── Rejected → Try alternative
    │   ├── Modified → Execute modified action
    │   └── Timeout → Use default action
    │
    └── Log response
```

---

## 5. Approval Triggers

### 5.1 When to Request Approval

```yaml
approval_triggers:
  # Low confidence
  low_confidence:
    threshold: 0.5
    action: request_approval
    
  # Sensitive operations
  sensitive_operations:
    - production_deployment
    - database_migration
    - security_change
    - cost_above_threshold
    
  # Critical steps
  critical_steps:
    - step_type: deployment
      action: request_approval
    - step_type: security_scan
      action: request_approval
      
  # Budget exceeded
  budget_exceeded:
    threshold: 1.00
    action: request_approval
    
  # Quality below threshold
  quality_below:
    threshold: 0.7
    action: request_approval
```

### 5.2 Approval Matrix

| Risk Level | Confidence | Action |
|------------|------------|--------|
| Low | > 0.8 | Auto-execute |
| Low | 0.5 - 0.8 | Auto-execute with monitoring |
| Low | < 0.5 | Request approval |
| Medium | > 0.8 | Auto-execute with monitoring |
| Medium | 0.5 - 0.8 | Request approval |
| Medium | < 0.5 | Request approval |
| High | > 0.8 | Request approval |
| High | 0.5 - 0.8 | Request approval |
| High | < 0.5 | Request approval |
| Critical | Any | Request approval |

---

## 6. Notification Channels

### 6.1 Channel Configuration

```yaml
notification_channels:
  email:
    enabled: true
    smtp_host: smtp.aida.dev
    from: approvals@aida.dev
    
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK_URL}
    channel: "#workflow-approvals"
    
  websocket:
    enabled: true
    endpoint: /ws/approvals
    
  in_app:
    enabled: true
    priority: high
```

### 6.2 Notification Template

```python
APPROVAL_NOTIFICATION = """
Workflow Approval Required

Workflow: {workflow_name}
Step: {step_name}
Type: {request_type}

Description:
{description}

AI Reasoning:
{ai_reasoning}

Confidence: {confidence}

Proposed Action:
{proposed_action}

Alternatives:
{alternatives}

Please respond within {timeout} minutes.

Response URL: {response_url}
"""
```

---

## 7. Response Handling

### 7.1 Response Types

| Response | Description | Action |
|----------|-------------|--------|
| `approved` | Human approves | Execute proposed action |
| `rejected` | Human rejects | Try alternative or skip |
| `modified` | Human modifies | Execute modified action |
| `timeout` | No response | Use default action |

### 7.2 Response Processing

```python
class ResponseHandler:
    async def handle_response(self, request: ApprovalRequest, response: dict):
        """Process human response."""
        
        if response["action"] == "approved":
            # Execute proposed action
            await self.execute_action(request.proposed_action)
            
        elif response["action"] == "rejected":
            # Try alternative
            if request.alternatives:
                await self.execute_action(request.alternatives[0])
            else:
                await self.skip_step(request.step_id)
                
        elif response["action"] == "modified":
            # Execute modified action
            await self.execute_action(response["modified_action"])
            
        elif response["action"] == "timeout":
            # Use default action
            await self.execute_default_action(request)
        
        # Update request status
        request.status = response["action"]
        request.response = response
        request.responded_at = datetime.utcnow()
        
        # Log response
        logger.info("approval_response",
            request_id=request.request_id,
            response=response["action"]
        )
```

---

## 8. Edit Plan

### 8.1 Plan Editing Interface

```python
class PlanEditor:
    async def edit_plan(
        self,
        workflow: Workflow,
        edits: list[PlanEdit]
    ) -> WorkflowPlan:
        """Edit workflow plan based on human input."""
        
        # Apply edits
        for edit in edits:
            if edit.type == "add_step":
                workflow.plan.add_step(edit.step)
            elif edit.type == "remove_step":
                workflow.plan.remove_step(edit.step_id)
            elif edit.type == "modify_step":
                workflow.plan.modify_step(edit.step_id, edit.changes)
            elif edit.type == "reorder_steps":
                workflow.plan.reorder(edit.new_order)
            elif edit.type == "change_agent":
                workflow.plan.change_agent(edit.step_id, edit.agent)
            elif edit.type == "change_model":
                workflow.plan.change_model(edit.step_id, edit.model)
        
        # Validate updated plan
        validated = self.validate_plan(workflow.plan)
        
        # Log edit
        logger.info("plan_edited",
            workflow_id=workflow.id,
            edits_count=len(edits)
        )
        
        return validated
```

### 8.2 Edit Types

| Edit Type | Description | Example |
|-----------|-------------|---------|
| `add_step` | Add new step | "Add security scan step" |
| `remove_step` | Remove step | "Remove documentation step" |
| `modify_step` | Modify step | "Change timeout to 300s" |
| `reorder_steps` | Reorder steps | "Run tests before deployment" |
| `change_agent` | Change agent | "Use security_agent instead" |
| `change_model` | Change model | "Use pro model for this step" |

---

## 9. Configuration

```yaml
human_in_the_loop:
  # Approval
  approval:
    enabled: true
    timeout: 3600s
    default_action: reject
    
  # Notifications
  notifications:
    enabled: true
    channels: [email, slack, websocket]
    
  # Edit plan
  edit_plan:
    enabled: true
    allow_add_steps: true
    allow_remove_steps: true
    allow_modify_steps: true
    
  # Monitoring
  monitoring:
    enabled: true
    log_approvals: true
    metrics_interval: 15s
```
