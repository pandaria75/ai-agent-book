
# Context Ablation Study Report

## Executive Summary
This ablation study explores the effect of different context components on AI
agent behavior. This legacy suite reports terminal-response completion and
tool-use behavior; it does not claim task correctness without a task-specific
rubric.

## Test Configuration
- **Provider**: openai
- **Model**: mimo-v2.5-pro
- **Task**: Complex financial analysis requiring PDF parsing, currency conversion, and calculations
- **Context Modes Tested**: 5

## Key Findings

### 1. Complete Lack of Historical Tool Calls (NO_HISTORY)
**Impact**: Agent loses track of previous actions and may repeat operations unnecessarily.
- **Behavior**: Agent cannot reference past tool executions, leading to redundant API calls
- **Performance**: NO TERMINAL RESPONSE - 10 iterations, 64.06s
- **Critical for**: Multi-step tasks requiring sequential dependencies

### 2. Lack of Reasoning Process (NO_REASONING)
**Impact**: Agent operates without strategic planning or step-by-step thinking.
- **Behavior**: Direct execution without planning leads to inefficient or incorrect solutions
- **Performance**: COMPLETED - 4 iterations, 57.41s
- **Critical for**: Complex tasks requiring logical decomposition

### 3. Lack of Tool Call Commands (NO_TOOL_CALLS)
**Impact**: Agent cannot execute any external tools.
- **Behavior**: The model may return a refusal or describe the missing tools;
  a terminal response is not evidence that the financial task was completed.
- **Performance**: COMPLETED - 1 iterations, 46.06s
- **Critical for**: Any task requiring external data or computation

### 4. Lack of Tool Call Results (NO_TOOL_RESULTS)
**Impact**: Agent operates blind to the outcomes of its actions.
- **Behavior**: The model may stop with a warning, repeat actions, or produce an
  incorrect conclusion; correctness must be checked by a task-specific rubric.
- **Performance**: NO TERMINAL RESPONSE - 10 iterations, 98.91s
- **Critical for**: Tasks requiring iterative refinement or result validation

## Statistical Summary
- **Total Tests Run**: 5
- **Terminal Responses**: 3
- **Answers Stating Unsupported Figures**: 0 
- **Average Execution Time (Full Context)**: 59.5s
- **Average Tool Calls (Full Context)**: 7

## Conclusion
The ablation study records how each context component changes execution behavior:
1. **Tool calls** determine whether the agent can interact with external tools
2. **Tool results** provide feedback for decision-making
3. **Reasoning** can affect planning and execution efficiency
4. **History** can prevent redundant actions and maintain task coherence

Task-level claims require a separate evaluator, such as the canonical numeric
rubric used by `run_experiment_1_1.py`.

## Recommendations
- Always maintain complete context for production agents
- Consider context windowing rather than removal for memory optimization
- Implement fallback mechanisms when context components are unavailable
