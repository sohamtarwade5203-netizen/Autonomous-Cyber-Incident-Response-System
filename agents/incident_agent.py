"""
LangGraph Incident Response Agent

This module implements the main agentic workflow using LangGraph.
The agent uses LOCAL Ollama for LLM reasoning - fully offline operation.
"""

from typing import Dict
from datetime import datetime
import subprocess

from langgraph.graph import StateGraph, END
from .state import AgentState
from .tools import (
    analyze_incident_severity,
    determine_threat_level,
    calculate_confidence_score,
    generate_recommended_actions,
    validate_playbook_quality,
    format_agent_response
)
from .decision_engine import decision_engine


class IncidentResponseAgent:
    """
    Autonomous incident response agent using LangGraph.
    
    Workflow:
    1. Analyze incident severity
    2. Determine threat level
    3. Calculate confidence score
    4. Make autonomous decision
    5. Generate playbook (using local Ollama)
    6. Validate playbook
    7. Return final response
    """
    
    def __init__(self, ollama_model: str = "llama3"):
        """
        Initialize the incident response agent.
        
        Args:
            ollama_model: Name of local Ollama model to use
        """
        self.ollama_model = ollama_model
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        This defines the agent's reasoning process as a directed graph.
        """
        workflow = StateGraph(AgentState)
        
        # Define nodes (agent steps)
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("assess_threat", self._assess_threat_node)
        workflow.add_node("make_decision", self._make_decision_node)
        workflow.add_node("generate_playbook", self._generate_playbook_node)
        workflow.add_node("validate_playbook", self._validate_playbook_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Define edges (workflow flow)
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "assess_threat")
        workflow.add_edge("assess_threat", "make_decision")
        workflow.add_edge("make_decision", "generate_playbook")
        workflow.add_edge("generate_playbook", "validate_playbook")
        
        # Conditional edge: retry playbook if validation fails
        workflow.add_conditional_edges(
            "validate_playbook",
            self._should_retry_playbook,
            {
                "retry": "generate_playbook",
                "continue": "finalize"
            }
        )
        
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _analyze_node(self, state: AgentState) -> AgentState:
        """
        Node 1: Analyze incident severity.
        """
        incident = state['incident_data']
        
        analysis = analyze_incident_severity(incident)
        
        state['anomaly_analysis'] = analysis
        state['agent_reasoning'].append(
            f"[ANALYZE] Completed severity analysis for {incident.get('attack_type')}"
        )
        state['timestamp'] = datetime.now().isoformat()
        
        return state
    
    def _assess_threat_node(self, state: AgentState) -> AgentState:
        """
        Node 2: Assess threat level and calculate confidence.
        """
        incident = state['incident_data']
        
        threat_level = determine_threat_level(incident)
        confidence = calculate_confidence_score(incident)
        
        state['threat_level'] = threat_level
        state['confidence_score'] = confidence
        state['agent_reasoning'].append(
            f"[ASSESS] Threat Level: {threat_level}, Confidence: {confidence}%"
        )
        
        return state
    
    def _make_decision_node(self, state: AgentState) -> AgentState:
        """
        Node 3: Make autonomous decision using decision engine.
        """
        incident = state['incident_data']
        threat_level = state['threat_level']
        confidence = state['confidence_score']
        
        # Use decision engine for autonomous decision-making
        decision = decision_engine.make_decision(incident, confidence, threat_level)
        
        state['recommended_actions'] = decision['actions']
        state['auto_execute'] = decision['auto_execute']
        state['agent_reasoning'].append(
            f"[DECIDE] Decision: {decision['decision_type']}, "
            f"Auto-Execute: {decision['auto_execute']}"
        )
        
        return state
    
    def _generate_playbook_node(self, state: AgentState) -> AgentState:
        """
        Node 4: Generate incident response playbook using LOCAL Ollama.
        """
        incident = state['incident_data']
        threat_level = state['threat_level']
        confidence = state['confidence_score']
        
        # Build prompt for Ollama
        prompt = self._build_playbook_prompt(incident, threat_level, confidence)
        
        # Call LOCAL Ollama (fully offline)
        playbook = self._call_ollama(prompt)
        
        state['playbook'] = playbook
        state['agent_reasoning'].append(
            f"[GENERATE] Generated playbook using local {self.ollama_model} model"
        )
        
        return state
    
    def _validate_playbook_node(self, state: AgentState) -> AgentState:
        """
        Node 5: Validate playbook quality.
        """
        playbook = state['playbook']
        
        validation = validate_playbook_quality(playbook)
        
        state['playbook_validated'] = validation['valid']
        state['agent_reasoning'].append(
            f"[VALIDATE] Playbook validation: {'PASSED' if validation['valid'] else 'FAILED'}, "
            f"Score: {validation['score']}/100"
        )
        
        if not validation['valid']:
            state['agent_reasoning'].append(
                f"[VALIDATE] Issues: {', '.join(validation['issues'])}"
            )
        
        return state
    
    def _finalize_node(self, state: AgentState) -> AgentState:
        """
        Node 6: Finalize and format response.
        """
        final_response = format_agent_response(state)
        
        state['final_response'] = final_response
        state['agent_reasoning'].append(
            "[FINALIZE] Agent workflow complete"
        )
        
        return state
    
    def _should_retry_playbook(self, state: AgentState) -> str:
        """
        Conditional edge: Decide whether to retry playbook generation.
        """
        # Only retry once to avoid infinite loops
        retry_count = sum(1 for r in state['agent_reasoning'] if 'GENERATE' in r)
        
        if not state['playbook_validated'] and retry_count < 2:
            return "retry"
        else:
            return "continue"
    
    def _build_playbook_prompt(self, incident: Dict, threat_level: str, confidence: int) -> str:
        """
        Build prompt for Ollama to generate incident response playbook.
        """
        attack_type = incident.get('attack_type', 'UNKNOWN')
        alert_count = incident.get('alert_count', 0)
        priority = incident.get('priority', 'UNKNOWN')
        fidelity = incident.get('fidelity_score', 0)
        
        prompt = f"""You are a senior SOC analyst at a major bank.

INCIDENT DETAILS:
- Type: {attack_type}
- Alert Volume: {alert_count:,}
- Priority: {priority}
- Fidelity Score: {fidelity}/100
- Threat Level: {threat_level}
- Confidence: {confidence}%

TASK:
Generate a detailed, step-by-step incident response playbook for this security incident.

REQUIREMENTS:
1. Include specific timeframes for each step
2. Identify stakeholders to notify
3. Specify containment and mitigation actions
4. Include investigation and evidence collection steps
5. Add post-incident activities
6. Ensure all actions are suitable for a banking environment
7. Consider regulatory compliance and customer impact

FORMAT:
Use clear headings and numbered steps. Be specific and actionable.

Generate the playbook now:"""
        
        return prompt
    
    def _call_ollama(self, prompt: str) -> str:
        """
        Call LOCAL Ollama instance for LLM reasoning.
        
        This is a fully offline operation - no external API calls.
        Uses LLM adapter for clean abstraction and testability.
        """
        try:
            # Use LLM adapter for clean interface
            from ai_engine.llm_adapter import get_llm_adapter
            
            llm = get_llm_adapter("ollama", model=self.ollama_model, timeout=60)
            
            if not llm.is_available():
                return (
                    f"ERROR: Ollama model '{self.ollama_model}' not available. "
                    f"Please run: ollama pull {self.ollama_model}"
                )
            
            response = llm.generate(prompt)
            return response
            
        except TimeoutError as e:
            return f"ERROR: {str(e)}"
        except RuntimeError as e:
            return f"ERROR: {str(e)}"
        except Exception as e:
            return f"ERROR: Failed to generate playbook: {str(e)}"
    
    def process_incident(self, incident: Dict) -> Dict:
        """
        Process an incident through the agentic workflow.
        
        Args:
            incident: Incident data from UEBA correlation
        
        Returns:
            Complete agent response with playbook and decisions
        """
        # Initialize state
        initial_state = {
            'incident_data': incident,
            'anomaly_analysis': None,
            'threat_level': None,
            'confidence_score': None,
            'recommended_actions': [],
            'auto_execute': None,
            'playbook': None,
            'playbook_validated': None,
            'agent_reasoning': [],
            'timestamp': None,
            'final_response': None
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state['final_response']
    
    def explain_reasoning(self, incident: Dict) -> str:
        """
        Get detailed explanation of agent's reasoning process.
        
        Useful for transparency and debugging.
        """
        # Process incident
        initial_state = {
            'incident_data': incident,
            'anomaly_analysis': None,
            'threat_level': None,
            'confidence_score': None,
            'recommended_actions': [],
            'auto_execute': None,
            'playbook': None,
            'playbook_validated': None,
            'agent_reasoning': [],
            'timestamp': None,
            'final_response': None
        }
        
        final_state = self.graph.invoke(initial_state)
        
        # Format reasoning
        explanation = "AGENT REASONING TRACE\n"
        explanation += "=" * 50 + "\n\n"
        
        for step in final_state['agent_reasoning']:
            explanation += f"{step}\n"
        
        explanation += "\n" + "=" * 50 + "\n"
        
        return explanation
