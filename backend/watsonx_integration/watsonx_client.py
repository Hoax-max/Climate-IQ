"""
IBM watsonx.ai integration for Climate Action Intelligence Platform
"""
import os
import logging
from typing import Dict, List, Optional, Any
from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from config import settings

logger = logging.getLogger(__name__)

class WatsonXClient:
    """Client for IBM watsonx.ai foundation models"""
    
    def __init__(self):
        self.credentials = {
            "url": settings.IBM_CLOUD_URL,
            "apikey": settings.IBM_CLOUD_API_KEY
        }
        self.project_id = settings.WATSONX_PROJECT_ID
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the watsonx.ai model"""
        try:
            parameters = {
                GenParams.DECODING_METHOD: "greedy",
                GenParams.MAX_NEW_TOKENS: 800,
                GenParams.MIN_NEW_TOKENS: 1,
                GenParams.TEMPERATURE: 0.1,
                GenParams.TOP_K: 50,
                GenParams.TOP_P: 1
            }
            
            self.model = Model(
                model_id=settings.WATSONX_MODEL_ID,
                params=parameters,
                credentials=self.credentials,
                project_id=self.project_id
            )
            logger.info("WatsonX model initialized successfully")
            self.use_fallback = False
            
        except Exception as e:
            logger.warning(f"WatsonX model unavailable, using fallback mode: {e}")
            self.model = None
            self.use_fallback = True
    
    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response using watsonx.ai or fallback"""
        if self.use_fallback:
            return self._generate_fallback_response(prompt, context)
            
        try:
            # Construct the full prompt with context
            full_prompt = self._construct_climate_prompt(prompt, context)
            
            # Generate response
            response = self.model.generate_text(prompt=full_prompt)
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._generate_fallback_response(prompt, context)
    
    def _generate_fallback_response(self, prompt: str, context: str = "") -> str:
        """Generate fallback response when Watson X.ai is unavailable"""
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ['carbon', 'footprint', 'emissions']):
            return """Based on climate data analysis, here are some key recommendations to reduce your carbon footprint:

🌱 **Energy Efficiency:**
- Switch to LED lighting (saves 75% energy)
- Use programmable thermostats
- Improve home insulation

🚗 **Transportation:**
- Consider electric or hybrid vehicles
- Use public transportation when possible
- Work from home when feasible

♻️ **Lifestyle Changes:**
- Reduce meat consumption
- Choose renewable energy sources
- Practice the 3 R's: Reduce, Reuse, Recycle

📊 **Impact:** These changes can reduce your carbon footprint by 20-40% annually."""

        elif any(word in prompt_lower for word in ['renewable', 'solar', 'wind', 'energy']):
            return """Here's information about renewable energy options:

☀️ **Solar Energy:**
- Residential solar panels can reduce electricity bills by 70-90%
- Average payback period: 6-10 years
- 25-year warranty typical

💨 **Wind Energy:**
- Small residential wind turbines available
- Best for rural areas with consistent wind

🔋 **Energy Storage:**
- Battery systems store excess renewable energy
- Provides backup power during outages

💡 **Getting Started:**
1. Conduct an energy audit
2. Research local incentives and rebates
3. Get quotes from certified installers
4. Consider community solar programs"""

        elif any(word in prompt_lower for word in ['climate', 'change', 'global', 'warming']):
            return """Climate change is one of the most pressing challenges of our time. Here's what you need to know:

🌡️ **Current Status:**
- Global temperatures have risen 1.1°C since pre-industrial times
- CO2 levels are at their highest in 3 million years
- Extreme weather events are becoming more frequent

🎯 **Goals:**
- Limit warming to 1.5°C (Paris Agreement)
- Achieve net-zero emissions by 2050
- Transition to renewable energy

🚀 **Solutions:**
- Renewable energy adoption
- Energy efficiency improvements
- Sustainable transportation
- Carbon capture technologies
- Individual action and policy changes

💪 **How You Can Help:**
- Reduce personal carbon footprint
- Support climate-friendly policies
- Choose sustainable products
- Educate others about climate action"""

        else:
            return """Thank you for your question about climate action! I'm here to help you make a positive environmental impact.

🌍 **I can assist you with:**
- Carbon footprint analysis and reduction strategies
- Renewable energy options and recommendations
- Sustainable lifestyle choices
- Climate change information and solutions
- Environmental impact tracking
- Local climate data and weather patterns

💡 **Popular topics:**
- Home energy efficiency
- Sustainable transportation
- Renewable energy systems
- Carbon offset programs
- Climate-friendly investments

Please feel free to ask specific questions about any of these topics, and I'll provide detailed, actionable advice!

*Note: Currently running in demonstration mode. Full AI capabilities will be available when IBM watsonx.ai service is accessible.*"""
    
    def _construct_climate_prompt(self, query: str, context: str) -> str:
        """Construct a climate-focused prompt"""
        system_prompt = """You are ClimateIQ, an AI assistant specialized in climate action and environmental sustainability. 
        You provide evidence-based, actionable advice for individuals, businesses, and communities to combat climate change.
        
        Guidelines:
        - Provide specific, actionable recommendations
        - Include quantifiable impact estimates when possible
        - Consider local context and feasibility
        - Reference scientific data and best practices
        - Be encouraging and solution-focused
        """
        
        if context:
            prompt = f"""{system_prompt}

Context Information:
{context}

User Question: {query}

Response:"""
        else:
            prompt = f"""{system_prompt}

User Question: {query}

Response:"""
        
        return prompt
    
    def analyze_climate_action(self, action_description: str, location: str = "") -> Dict[str, Any]:
        """Analyze a climate action for impact and feasibility"""
        prompt = f"""
        Analyze the following climate action for its environmental impact and implementation feasibility:
        
        Action: {action_description}
        Location: {location}
        
        Please provide:
        1. Estimated CO2 reduction potential (kg/year)
        2. Implementation difficulty (1-5 scale)
        3. Cost estimate (Low/Medium/High)
        4. Timeline for implementation
        5. Additional environmental benefits
        6. Potential challenges
        
        Format your response as structured data.
        """
        
        response = self.generate_response(prompt)
        return self._parse_action_analysis(response)
    
    def _parse_action_analysis(self, response: str) -> Dict[str, Any]:
        """Parse the action analysis response into structured data"""
        # Simple parsing - in production, you'd want more robust parsing
        analysis = {
            "co2_reduction": "To be calculated",
            "difficulty": 3,
            "cost": "Medium",
            "timeline": "3-6 months",
            "benefits": [],
            "challenges": [],
            "raw_response": response
        }
        
        return analysis
    
    def generate_personalized_plan(self, user_profile: Dict[str, Any], context: str = "") -> str:
        """Generate personalized climate action plan"""
        prompt = f"""
        Create a personalized climate action plan for a user with the following profile:
        
        Location: {user_profile.get('location', 'Not specified')}
        Lifestyle: {user_profile.get('lifestyle', 'Not specified')}
        Household Size: {user_profile.get('household_size', 'Not specified')}
        Current Actions: {user_profile.get('current_actions', 'None specified')}
        Interests: {user_profile.get('interests', 'General environmental')}
        Budget: {user_profile.get('budget', 'Not specified')}
        
        Please provide:
        1. Top 5 priority actions ranked by impact
        2. Specific implementation steps for each action
        3. Expected environmental impact
        4. Cost estimates and potential savings
        5. Timeline for implementation
        6. Local resources and incentives available
        
        Make the plan practical, achievable, and tailored to their specific situation.
        """
        
        return self.generate_response(prompt, context)