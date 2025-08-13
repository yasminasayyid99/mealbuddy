import requests
from flask import current_app
import json

class ChatAnywhereService:
    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key or current_app.config.get('CHATANYWHERE_API_KEY')
        self.base_url = base_url or current_app.config.get('CHATANYWHERE_BASE_URL')
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def chat_completion(self, message, context=None):
        """Send message to ChatAnywhere API and get response"""
        try:
            # Prepare system message for food/restaurant context
            system_message = {
                "role": "system",
                "content": "You are a helpful AI assistant for a food meetup app called MealBuddy. Help users with food recommendations, restaurant suggestions, meal planning, and organizing food-related events. Be friendly, informative, and focus on food and dining experiences."
            }
            
            messages = [system_message]
            
            # Add context if provided
            if context:
                context_message = {
                    "role": "system",
                    "content": f"Additional context: {context}"
                }
                messages.append(context_message)
            
            # Add user message
            user_message = {
                "role": "user",
                "content": message
            }
            messages.append(user_message)
            
            # Make API request
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message': result['choices'][0]['message']['content'],
                    'usage': result.get('usage', {})
                }
            else:
                return {
                    'success': False,
                    'error': f"API request failed with status {response.status_code}",
                    'details': response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"Network error: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }
    
    def get_restaurant_recommendation(self, cuisine_type, location, budget=None, dietary_restrictions=None):
        """Get restaurant recommendations based on preferences"""
        message = f"Recommend restaurants for {cuisine_type} cuisine in {location}."
        
        if budget:
            message += f" Budget range: {budget}."
        if dietary_restrictions:
            message += f" Dietary restrictions: {', '.join(dietary_restrictions)}."
            
        message += " Please provide 3-5 specific restaurant recommendations with brief descriptions."
        
        return self.chat_completion(message)
    
    def get_food_recommendation(self, preferences, location=None, budget=None):
        """Get food recommendations based on user preferences"""
        message = f"Suggest food options based on these preferences: {preferences}."
        
        if location:
            message += f" Location: {location}."
        if budget:
            message += f" Budget: {budget}."
            
        message += " Please provide specific food suggestions and where to find them."
        
        return self.chat_completion(message)
    
    def get_event_suggestions(self, category, participants_count=None):
        """Get suggestions for food-related events"""
        message = f"Suggest {category} food events or activities."
        
        if participants_count:
            message += f" For {participants_count} people."
            
        message += " Please provide creative and engaging food-related event ideas."
        
        context = "Focus on events that bring people together around food, such as cooking classes, food tours, restaurant meetups, potluck dinners, etc."
        
        return self.chat_completion(message, context)

# Factory function to create service instance
def get_ai_service():
    """Get AI service instance with current app context"""
    return ChatAnywhereService()

# For backward compatibility, create a lazy instance
class LazyAIService:
    def __init__(self):
        self._service = None
    
    def __getattr__(self, name):
        if self._service is None:
            self._service = get_ai_service()
        return getattr(self._service, name)

ai_service = LazyAIService()