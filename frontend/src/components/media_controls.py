import flet as ft
import sys
import os
import speech_recognition as sr
import asyncio
from threading import Thread
from agents import ItemHelpers, MessageOutputItem, Runner, trace
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from src.components.media_display import VoiceAnimation
from src.components.hand_drawing_recognition import HandDrawingRecognition
from controller.agent import agent as hangman_agent, manager as agent_game_manager
import inspect

# Print debugging info about the imported GameStateManager from agent
print(f"MediaControls using agent's GameStateManager from: {inspect.getmodule(agent_game_manager).__file__}")
print(f"Agent's GameStateManager instance: {id(agent_game_manager)}")

class MediaControls:
    def __init__(self, show_notification_callback, on_guess_callback):
        self.show_notification = show_notification_callback
        self.on_guess = on_guess_callback
        
        # Store reference to agent's GameStateManager
        self.agent_game_manager = agent_game_manager
        print(f"MediaControls initialized with agent's game manager: {id(self.agent_game_manager)}")
        
        # Media display components
        self.voice_animation = VoiceAnimation()
        self.hand_drawing = HandDrawingRecognition(on_prediction_callback=self._handle_drawing_prediction)
        
        # Agent chat components
        self.agent_inputs = []  # Store conversation history
        self.conversation_id = None  # Will be initialized when chat starts
        self.chat_history = None  # Will be set in _create_chat_view
        self.chat_input = None  # Will be set in _create_chat_view
        self.send_button = None  # Will be set in _create_chat_view
        
        # Voice recording attributes
        self.recording = False
        self.recognizer = None
        self.source = None
        self.audio = None
        
        # Voice recognition for chat - NEW
        self.is_recording_voice_for_chat = False
        self.mic_button = ft.IconButton(
            icon=ft.Icons.MIC,
            tooltip="Voice to text",
            on_click=self._toggle_voice_to_text
        )
        
        # Voice control buttons
        self.voice_start_btn = ft.ElevatedButton(
            "Start Voice Input",
            icon=ft.Icons.MIC,
            on_click=self._start_voice_recording,
            style=config.BUTTON_STYLE,
            visible=True
        )
        
        self.voice_stop_btn = ft.ElevatedButton(
            "Stop Voice Input",
            icon=ft.Icons.MIC_OFF,
            on_click=self._stop_voice_recording,
            style=config.BUTTON_STYLE,
            visible=True
        )
        
        # Hand drawing control buttons
        self.drawing_start_btn = ft.ElevatedButton(
            "Start Hand Drawing",
            icon=ft.Icons.DRAW,
            on_click=self._start_hand_drawing,
            style=config.BUTTON_STYLE,
            visible=True
        )
        
        self.drawing_stop_btn = ft.ElevatedButton(
            "Stop Hand Drawing",
            icon=ft.Icons.CANCEL,
            on_click=self._stop_hand_drawing,
            style=config.BUTTON_STYLE,
            visible=True
        )
        
        self.drawing_clear_btn = ft.ElevatedButton(
            "Clear Canvas",
            icon=ft.Icons.CLEAR,
            on_click=self._clear_drawing_canvas,
            style=config.BUTTON_STYLE,
            visible=True
        )
        
        self.drawing_recognize_btn = ft.ElevatedButton(
            "Recognize Letter",
            icon=ft.Icons.SEARCH,
            on_click=self._recognize_drawn_letter,
            style=config.BUTTON_STYLE,
            visible=True
        )
        
        # Currently active view (to track which one is open)
        self.active_view = None
        self.current_tab = "chat"  # Changed default tab to chat
        
        # Create views first
        self.voice_view = self._create_voice_view()
        self.drawing_view = self._create_drawing_view()
        self.chat_view = self._create_chat_view()

        # Initialize view container
        self.view_container = ft.Container(
            content=self.chat_view,  # Default to chat view
            expand=True
        )
        
        # Create the Cupertino navigation bar
        self.navigation_bar = self._create_navigation_bar()
        
        # Main container that holds everything
        self.container = ft.Column(
            controls=[
                self.navigation_bar,
                self.view_container
            ],
            expand=True
        )

    def _create_navigation_bar(self):
        """Create a Cupertino navigation bar for switching between views"""
        return ft.NavigationBar(
            bgcolor=ft.colors.WHITE,
            selected_index=2,  # Start with Chat selected
            indicator_color=ft.colors.BLUE_800,  # Set selected background to blue
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.icons.MIC_OUTLINED,
                    selected_icon=ft.icons.MIC,
                    label="Voice"
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.DRAW_OUTLINED,
                    selected_icon=ft.icons.DRAW,
                    label="Drawing"
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.CHAT_OUTLINED,
                    selected_icon=ft.icons.CHAT,
                    label="Chat"
                ),
            ],
            on_change=self._handle_tab_change
        )

    def build(self):
        """Return the main container"""
        return self.container
        
    def _handle_tab_change(self, e):
        """Handle navigation rail tab change"""
        index = e.control.selected_index
        
        # Reset any active views
        self._reset_all_views()
        
        # Switch to the selected view
        if index == 0:  # Voice input
            self.current_tab = "voice"
            self.view_container.content = self.voice_view
        elif index == 1:  # Drawing
            self.current_tab = "drawing"
            self.view_container.content = self.drawing_view
        elif index == 2:  # Chat view
            self.current_tab = "chat"
            print("===MEDIA_CONTROLS=== Switching to chat view")
            
            try:
                # Simply switch back to the existing chat view - don't recreate it
                # This preserves the conversation history and agent state
                self.view_container.content = self.chat_view
                
                # Ensure the input components are properly referenced and enabled
                # This fixes the issue where input becomes non-functional after switching back
                self._refresh_chat_input_references()
                
            except Exception as e:
                print(f"===MEDIA_CONTROLS=== Error switching to chat view: {e}")
                import traceback
                traceback.print_exc()
                
                # If there's an error, try to recreate the chat view as a fallback
                try:
                    print("===MEDIA_CONTROLS=== Attempting to recreate chat view as fallback")
                    # Save existing conversation history
                    old_history = []
                    if self.chat_history and hasattr(self.chat_history, 'controls'):
                        old_history = self.chat_history.controls.copy()
                    
                    # Recreate chat view
                    self.chat_view = self._create_chat_view()
                    self.view_container.content = self.chat_view
                    
                    # Restore history if we had any
                    if old_history and self.chat_history:
                        self.chat_history.controls.clear()
                        self.chat_history.controls.extend(old_history)
                        self.chat_history.update()
                        
                except Exception as recreate_error:
                    print(f"===MEDIA_CONTROLS=== Failed to recreate chat view: {recreate_error}")
            
        self.view_container.update()
            
    def _create_voice_view(self):
        """Create the voice input view"""
        return ft.Column([
            ft.Text("Voice Input", style=config.TITLE_STYLE),
            self.voice_animation,
            ft.Row([self.voice_start_btn, self.voice_stop_btn], 
                   alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
        
    def _create_drawing_view(self):
        """Create the hand drawing view"""
        return ft.Column([
            ft.Text("Hand Drawing", style=config.TITLE_STYLE),
            ft.Container(
                content=ft.Column([
                    self.hand_drawing,
                    ft.Container(height=2),  # Minimal spacer
                    ft.Column([
                        ft.Row([self.drawing_start_btn, self.drawing_stop_btn], 
                               alignment=ft.MainAxisAlignment.CENTER),
                        ft.Row([self.drawing_clear_btn, self.drawing_recognize_btn], 
                               alignment=ft.MainAxisAlignment.CENTER),
                    ], spacing=4),
                ], spacing=4),
                margin=0,
                padding=0
            ),
        ], alignment=ft.MainAxisAlignment.START, spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        
    def _create_chat_view(self):
        """Create a chat view that aligns with the hangman text height"""
        # Chat history display
        self.chat_history = ft.ListView(
            spacing=10,
            padding=10,
            auto_scroll=True,
            expand=True,
            height=400,  # Set a fixed height to match the hangman content area
        )

        # Initial welcome message
        self.chat_history.controls.append(
            ft.Container(
                content=ft.Text("Welcome to Hangman Chat! I'll help you play the game. Type your message or use voice input.", 
                                color=ft.Colors.BLACK),
                bgcolor=ft.Colors.BLUE_50,
                border_radius=ft.border_radius.all(10),
                padding=10,
                width=300,
                alignment=ft.alignment.center_left
            )
        )
        
        # Text input field for chat functionality - enabled now
        self.chat_input = ft.TextField(
            hint_text="Type your message...",
            border=ft.InputBorder.OUTLINE,
            expand=True,
            color=ft.Colors.BLACK,  # Make text darker for better visibility
            on_submit=self._send_message,  # Enable submitting with Enter key
        )
        
        # Send button - enabled now
        self.send_button = ft.IconButton(
            icon=ft.Icons.SEND,
            tooltip="Send message",
            on_click=self._send_message
        )

        return ft.Column([
            # Header with title aligned with game panel
            ft.Text("Agent Chat", style=config.TITLE_STYLE),
            # ft.Divider(height=10),
                   
            # Chat history container (takes most space)
            ft.Container(
                content=self.chat_history,
                border=ft.border.all(2, config.COLOR_PALETTE["secondary"]),
                border_radius=10,
                padding=10,
                expand=True,
                height=650,  # Increased height for better visibility
            ),
            
            # Input area for chat functionality
            ft.Row([
                self.chat_input,
                self.send_button,
                self.mic_button  # Add mic button to the chat input row
            ], spacing=10)
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
        
    def _start_voice_recording(self, e):
        """Start voice recording session"""
        if self.recording:
            return  # Already recording
            
        # Check if there's already a detected letter displayed
        if hasattr(self.voice_animation.letter_display, 'value') and self.voice_animation.letter_display.value and len(self.voice_animation.letter_display.value) == 1 and self.voice_animation.letter_display.value.isalpha():
            # Clear the previous detection before starting new recording
            self.voice_animation.letter_display.value = "Listening..."
            self.voice_animation.letter_display.color = ft.Colors.BLUE_600
            self.voice_animation.letter_display.size = 32
            self.voice_animation.letter_display.update()
        
        self._reset_all_views()
        self.active_view = "voice"
        self.voice_animation.toggle_recording()
        
        # Initialize voice recognition
        self.recording = True
        self.recognizer = sr.Recognizer()
        self.source = sr.Microphone()
        
        # Start recording in a separate thread to avoid blocking the UI
        Thread(target=self._voice_recording_worker).start()
    
    def _voice_recording_worker(self):
        """Worker thread to handle voice recording"""
        try:
            with self.source as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                self.audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=5)
                
                # Only process if still recording (user didn't stop manually)
                if self.recording:
                    self._process_voice_recognition()
                    
        except sr.WaitTimeoutError:
            if self.recording:  # Only show timeout if user didn't manually stop
                self.voice_animation.letter_display.value = "Timeout"
                self.voice_animation.letter_display.color = ft.Colors.AMBER_600
                self.voice_animation.letter_display.size = 28
                self.voice_animation.letter_display.update()
        except Exception as e:
            if self.recording:  # Only show error if user didn't manually stop
                self.voice_animation.letter_display.value = "Error"
                self.voice_animation.letter_display.color = ft.Colors.RED_600
                self.voice_animation.letter_display.size = 24
                self.voice_animation.letter_display.update()
                print(f"Voice recording error: {e}")
        finally:
            # Clean up and stop recording
            self._finalize_voice_recording()
    
    def _process_voice_recognition(self):
        """Process the recorded audio and recognize speech"""
        try:
            text = self.recognizer.recognize_google(self.audio, language="en-US").strip().upper()
            if text.startswith("LETTER "):
                possible_letter = text.replace("LETTER ", "").strip()

                if len(possible_letter) == 1 and possible_letter.isalpha():
                    self.voice_animation.letter_display.value = possible_letter
                    self.voice_animation.letter_display.color = ft.Colors.GREEN_600
                    self.voice_animation.letter_display.size = 56
                    self.voice_animation.letter_display.update()
                    
                    # Process the guess immediately
                    self.on_guess(possible_letter)
                else:
                    self.voice_animation.letter_display.value = "Invalid"
                    self.voice_animation.letter_display.color = ft.Colors.RED_600
                    self.voice_animation.letter_display.size = 32
                    self.voice_animation.letter_display.update()
            else:
                self.voice_animation.letter_display.value = "Say 'Letter X'"
                self.voice_animation.letter_display.color = ft.Colors.ORANGE_600
                self.voice_animation.letter_display.size = 28
                self.voice_animation.letter_display.update()
                
        except sr.UnknownValueError:
            self.voice_animation.letter_display.value = "Didn't understand"
            self.voice_animation.letter_display.color = ft.Colors.GREY_600
            self.voice_animation.letter_display.size = 24
            self.voice_animation.letter_display.update()
        except sr.RequestError:
            self.voice_animation.letter_display.value = "Service Error"
            self.voice_animation.letter_display.color = ft.Colors.RED_600
            self.voice_animation.letter_display.size = 24
            self.voice_animation.letter_display.update()
    
    def _finalize_voice_recording(self):
        """Clean up after voice recording is complete"""
        self.recording = False
        # Stop the recording animation but keep the detected letter displayed
        self.voice_animation.stop_recording_preserve_letter()
        self.active_view = None
    
    def _stop_voice_recording(self, e):
        """Stop recording manually"""
        if not self.recording:
            return  # Not recording
            
        print("===MEDIA_CONTROLS=== Manually stopping voice recording")
        
        # Set recording to False to signal the worker thread to stop
        self.recording = False
        
        # Stop the animation and show stopped message
        self.voice_animation.letter_display.value = "Recording Stopped"
        self.voice_animation.letter_display.color = ft.Colors.ORANGE_600
        self.voice_animation.letter_display.size = 28
        self.voice_animation.letter_display.update()
        
        # Stop the recording animation
        self.voice_animation.stop_recording_preserve_letter()
        self.active_view = None
    
    def _start_hand_drawing(self, e):
        self._reset_all_views()
        self.active_view = "drawing"
        self.hand_drawing.start_camera()
        # Display status in the drawing UI instead of notification
    
    def _stop_hand_drawing(self, e):
        if self.active_view == "drawing":
            self.hand_drawing.stop_camera()
            self.active_view = None
            # Status is shown in the UI instead of notification
    
    def _clear_drawing_canvas(self, e):
        if self.active_view == "drawing":
            self.hand_drawing.clear_canvas()
            # Status is shown in the UI instead of notification
    
    def _recognize_drawn_letter(self, e):
        if self.active_view == "drawing":
            # Recognize the letter - no need to show notification here anymore
            prediction, confidence = self.hand_drawing.recognize_letter()
            
            # If the recognition returned a valid prediction directly
            if prediction and confidence > 0.5:
                self.on_guess(prediction)
                # Instead of a notification, the result is displayed in the UI
            # The UI will show a message if confidence is insufficient
    
    def _handle_drawing_prediction(self, prediction, confidence):
        """Handle prediction result from hand drawing recognition"""
        if confidence > 0.5:  # Only use prediction if confidence is reasonable
            self.on_guess(prediction)
    
    def _reset_all_views(self):
        """Reset all views before activating a new one"""
        # Stop voice recording if active
        if self.recording:
            self.recording = False
            
        self.voice_animation.stop_recording()
        self.hand_drawing.stop_camera()
        self.active_view = None
        
    def reset(self):
        """Reset all media controls"""
        print("===MEDIA_CONTROLS=== Resetting media controls")
        
        # Reset all UI views first
        self._reset_all_views()
        
        # Check current game state after reset
        if self.agent_game_manager.current_game:
            current_state = self.agent_game_manager._get_state()
            print(f"===MEDIA_CONTROLS=== Current game after UI reset: word={self.agent_game_manager.current_game.secret_word}, display={current_state.display_word}")
        else:
            print("===MEDIA_CONTROLS=== No active game found after UI reset")
        
        # Clear and reset the chat history
        self.reset_chat()
        
        # Create a new conversation ID to start fresh
        import uuid
        self.conversation_id = str(uuid.uuid4().hex[:16])
        print(f"===MEDIA_CONTROLS=== Created new conversation with ID: {self.conversation_id}")
        
        # Clear the agent inputs as well
        self.agent_inputs = []
        
    def create_panel(self):
        """Create the left panel with media controls"""
        return ft.Container(
            content=self.container,
            expand=1,  # Take up 1 part of the space
            padding=20,
        )
    
    def _send_message(self, e):
        """Send a user message to the agent and get a response"""
        # Ensure we have valid references to the input components
        if not self.chat_input:
            print("===MEDIA_CONTROLS=== Chat input reference is None, refreshing references")
            self._refresh_chat_input_references()
            if not self.chat_input:
                print("===MEDIA_CONTROLS=== Still no valid chat input reference after refresh")
                return
        
        # Get user message from input field
        message = self.chat_input.value
        if not message or message.strip() == "":
            return  # Don't send empty messages
            
        # Clear the input field
        self.chat_input.value = ""
        self.chat_input.update()
        
        # Add user message to chat history
        self._add_user_message(message)
        
        # Disable input while processing
        self._set_input_state(disabled=True)
        
        # Start a background thread to handle the agent interaction
        Thread(target=asyncio.run, args=(self._process_agent_response(message),)).start()
    
    def _add_user_message(self, message):
        """Add a user message to the chat history"""
        try:
            if not self.chat_history:
                print("===MEDIA_CONTROLS=== chat_history is None, cannot add user message")
                return
                
            self.chat_history.controls.append(
                ft.Container(
                    content=ft.Text(message, color=ft.Colors.BLACK),
                    bgcolor=ft.Colors.GREY_200,
                    border_radius=ft.border_radius.all(10),
                    padding=10,
                    width=300,
                    alignment=ft.alignment.center_right
                )
            )
            
            # Only update if the chat history is properly attached to the page
            if hasattr(self.chat_history, 'page') and self.chat_history.page and self.current_tab == "chat":
                self.chat_history.update()
                print("===MEDIA_CONTROLS=== Successfully updated chat history with user message")
            else:
                print("===MEDIA_CONTROLS=== Chat history not attached to page, message added but not updated")
                # Try to update the entire view container instead
                if self.view_container and hasattr(self.view_container, 'page') and self.view_container.page:
                    self.view_container.update()
                    print("===MEDIA_CONTROLS=== Updated view container instead")
                    
        except Exception as e:
            print(f"===MEDIA_CONTROLS=== Error adding user message: {e}")
            import traceback
            traceback.print_exc()
    
    def _add_agent_message(self, message):
        """Add an agent message to the chat history"""
        try:
            # Check if chat_history needs to be reinitialized
            if not self.chat_history:
                print("===MEDIA_CONTROLS=== chat_history is None, attempting to reinitialize")
                # Try to get chat_history from the current chat view
                if self.chat_view and hasattr(self.chat_view, 'controls') and len(self.chat_view.controls) > 1:
                    chat_container = self.chat_view.controls[1]  # Chat history container
                    if hasattr(chat_container, 'content'):
                        self.chat_history = chat_container.content
                        print("===MEDIA_CONTROLS=== Reinitialized chat_history from chat view")
                
            if not self.chat_history:
                print("===MEDIA_CONTROLS=== Still no chat_history, cannot add agent message")
                return
                
            self.chat_history.controls.append(
                ft.Container(
                    content=ft.Text(message, color=ft.Colors.BLACK),
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=ft.border_radius.all(10),
                    padding=10,
                    width=300,
                    alignment=ft.alignment.center_left
                )
            )
            
            # Only update if the chat view is currently active and properly attached
            if self.current_tab == "chat":
                if hasattr(self.chat_history, 'page') and self.chat_history.page:
                    self.chat_history.update()
                    print("===MEDIA_CONTROLS=== Successfully updated chat history with agent message")
                else:
                    print("===MEDIA_CONTROLS=== Chat history not attached to page, trying view container update")
                    # Try to update the entire view container instead
                    if self.view_container and hasattr(self.view_container, 'page') and self.view_container.page:
                        self.view_container.update()
                        print("===MEDIA_CONTROLS=== Updated view container with agent message")
            else:
                print(f"===MEDIA_CONTROLS=== Not in chat tab (current: {self.current_tab}), message added but not updated")
                
        except Exception as e:
            print(f"===MEDIA_CONTROLS=== Error adding agent message: {e}")
            import traceback
            traceback.print_exc()
    
    def _switch_to_view(self, view_name):
        """Switch to a specific view programmatically"""
        view_index = {"voice": 0, "drawing": 1, "chat": 2}
        if view_name in view_index:
            # Switch to view first
            self.navigation_bar.selected_index = view_index[view_name]
            # Always use the tab change handler to ensure proper view initialization
            self._handle_tab_change(type('Event', (), {'control': self.navigation_bar})())
            
    async def _process_agent_response(self, message):
        """Process the user message and get a response from the agent"""
        try:
            # Initialize conversation ID if first message
            if not self.conversation_id:
                import uuid
                self.conversation_id = str(uuid.uuid4().hex[:16])
                print(f"===MEDIA_CONTROLS=== Initialized new conversation with ID: {self.conversation_id}")
            
            # Check for view switching commands before sending to agent
            lower_message = message.lower()
            if "chat" in lower_message or "type" in lower_message:
                self._switch_to_view("chat")
                await asyncio.sleep(0.1)  # Give UI time to update
                await asyncio.get_event_loop().run_in_executor(None, self._add_agent_message,
                    "I've switched back to chat mode. You can type your letters here.")
                return
            elif "draw" in lower_message and ("letter" in lower_message or "want" in lower_message):
                self._switch_to_view("drawing")
                await asyncio.sleep(0.1)  # Give UI time to update
                await asyncio.get_event_loop().run_in_executor(None, self._add_agent_message, 
                    "I've switched to drawing mode. You can now draw your letter on the canvas.")
                return
            elif "voice" in lower_message and ("say" in lower_message or "want" in lower_message or "speak" in lower_message):
                self._switch_to_view("voice")
                await asyncio.sleep(0.1)  # Give UI time to update
                await asyncio.get_event_loop().run_in_executor(None, self._add_agent_message, 
                    "I've switched to voice mode. You can now say your letter starting with 'Letter' followed by your guess.")
                return
            
            # Check if this is a message that might contain a letter guess
            is_letter_guess = False
            if len(message) == 1 and message.isalpha():
                # Direct single letter input
                is_letter_guess = True
                print(f"===MEDIA_CONTROLS=== Direct letter input detected: {message}")
            elif "guess" in lower_message.lower() and "letter" in lower_message.lower():
                # Message about guessing a letter
                is_letter_guess = True
                print(f"===MEDIA_CONTROLS=== Letter guess request detected in: {message}")
            
            # If this is a letter guess, check game state first
            if is_letter_guess:
                if self.agent_game_manager.current_game:
                    print(f"===MEDIA_CONTROLS=== Current game before guess: {self.agent_game_manager.current_game.secret_word}, display: {self.agent_game_manager._get_state().display_word}")
                    # Add a message to explicitly sync with the game
                    self.agent_inputs.append({"content": "sync with the current game first", "role": "user"})
                else:
                    print("===MEDIA_CONTROLS=== No active game found before letter guess")
            
            # Add message to agent inputs
            self.agent_inputs.append({"content": message, "role": "user"})
            
            # Run the agent within a trace
            print("===MEDIA_CONTROLS=== Running agent with user message")
            with trace("Game Agent", group_id=self.conversation_id):
                result = await Runner.run(hangman_agent, input=self.agent_inputs)
                
                # Process the agent's response
                for item in result.new_items:
                    if isinstance(item, MessageOutputItem):
                        text = ItemHelpers.text_message_output(item)
                        if text:
                            print(f"===MEDIA_CONTROLS=== Agent response: {text[:50]}...")
                            # Update the UI in the main thread
                            await asyncio.get_event_loop().run_in_executor(None, self._add_agent_message, text)
                            
                            # Check if the agent's response contains a guess to process
                            self._process_agent_guess(text)
            
            # Check game state after agent processing and ensure UI sync
            if self.agent_game_manager.current_game:
                print(f"===MEDIA_CONTROLS=== After agent response - current game word: {self.agent_game_manager.current_game.secret_word}")
                print(f"===MEDIA_CONTROLS=== Game status: {self.agent_game_manager._get_state().game_status}")
                print(f"===MEDIA_CONTROLS=== Current display: {self.agent_game_manager._get_state().display_word}")
                # Ensure the UI is in sync with the current game state
                await asyncio.get_event_loop().run_in_executor(None, self.ensure_ui_synced_with_game)
            else:
                print("===MEDIA_CONTROLS=== No active game after agent response")
                
            # Update inputs for the next conversation turn
            self.agent_inputs = result.to_input_list()
            
            # Re-enable the chat input
            await asyncio.get_event_loop().run_in_executor(None, self._set_input_state, False)
        
        except Exception as e:
            error_message = f"Error processing message: {str(e)}"
            print(f"===MEDIA_CONTROLS=== Exception in _process_agent_response: {str(e)}")
            await asyncio.get_event_loop().run_in_executor(None, self._add_agent_message, error_message)
            await asyncio.get_event_loop().run_in_executor(None, self._set_input_state, False)
    
    def _process_agent_guess(self, message):
        """Check if agent message contains a letter guess and process it"""
        print(f"===MEDIA_CONTROLS=== Processing potential guess from message: {message[:50]}...")
        
        # Several patterns to recognize a letter guess
        letter_patterns = [
            "suggested the letter",
            "Hai proposto la lettera",
            "guessed the letter",
            "letter",
            # Add more patterns as needed
        ]
        
        # Check if this message is about an active game (only process if active game)
        if not self.agent_game_manager.current_game:
            print("===MEDIA_CONTROLS=== No active game, skipping letter extraction")
            return
            
        # Look for patterns that indicate the agent has guessed a letter
        found_letter = None
        
        # Try to extract letter from quotes
        if "'" in message or '"' in message:
            for pattern in letter_patterns:
                if pattern in message.lower():
                    try:
                        # Try to extract letter from the message (inside quotes)
                        # First look for single quotes
                        if "'" in message:
                            start_index = message.find("'") + 1
                            end_index = message.find("'", start_index)
                            if start_index > 0 and end_index > start_index:
                                potential_letter = message[start_index:end_index]
                                if len(potential_letter) == 1 and potential_letter.isalpha():
                                    found_letter = potential_letter
                                    print(f"===MEDIA_CONTROLS=== Extracted letter from single quotes: {found_letter}")
                                    break
                        # If not found in single quotes, try double quotes
                        elif '"' in message:
                            start_index = message.find('"') + 1
                            end_index = message.find('"', start_index)
                            if start_index > 0 and end_index > start_index:
                                potential_letter = message[start_index:end_index]
                                if len(potential_letter) == 1 and potential_letter.isalpha():
                                    found_letter = potential_letter
                                    print(f"===MEDIA_CONTROLS=== Extracted letter from double quotes: {found_letter}")
                                    break
                    except Exception as e:
                        print(f"===MEDIA_CONTROLS=== Error extracting letter: {e}")
        
        # If we found a letter, process it
        if found_letter:
            print(f"===MEDIA_CONTROLS=== Processing letter guess: {found_letter}")
            # Convert to uppercase if needed
            found_letter = found_letter.upper()
            
            # Make sure it's not already in the guessed letters
            current_state = self.agent_game_manager._get_state()
            if current_state and found_letter in current_state.guessed_letters:
                print(f"===MEDIA_CONTROLS=== Letter {found_letter} already guessed, skipping")
                return
                
            # Pass to the on_guess callback
            try:
                self.on_guess(found_letter)
                print(f"===MEDIA_CONTROLS=== Successfully processed letter guess: {found_letter}")
            except Exception as e:
                print(f"===MEDIA_CONTROLS=== Error in on_guess callback: {e}")
    
    def _set_input_state(self, disabled=False):
        """Enable or disable the chat input components"""
        try:
            print(f"===MEDIA_CONTROLS=== Setting input state, disabled={disabled}")
            
            # Check and update chat_input
            if self.chat_input:
                try:
                    self.chat_input.disabled = disabled
                    self.chat_input.update()
                    print("===MEDIA_CONTROLS=== Updated chat_input state")
                except Exception as e:
                    print(f"===MEDIA_CONTROLS=== Error updating chat_input: {e}")
            else:
                print("===MEDIA_CONTROLS=== chat_input is None")
                
            # Check and update send_button
            if self.send_button:
                try:
                    self.send_button.disabled = disabled
                    self.send_button.update()
                    print("===MEDIA_CONTROLS=== Updated send_button state")
                except Exception as e:
                    print(f"===MEDIA_CONTROLS=== Error updating send_button: {e}")
            else:
                print("===MEDIA_CONTROLS=== send_button is None")
                
            # Check and update mic_button
            if self.mic_button:
                try:
                    self.mic_button.disabled = disabled
                    self.mic_button.update()
                    print("===MEDIA_CONTROLS=== Updated mic_button state")
                except Exception as e:
                    print(f"===MEDIA_CONTROLS=== Error updating mic_button: {e}")
            else:
                print("===MEDIA_CONTROLS=== mic_button is None")
                
        except Exception as e:
            print(f"===MEDIA_CONTROLS=== Error setting input state: {e}")
            import traceback
            traceback.print_exc()
            
            # Try to refresh references if there's an error
            try:
                print("===MEDIA_CONTROLS=== Attempting to refresh references due to error")
                self._refresh_chat_input_references()
            except Exception as refresh_error:
                print(f"===MEDIA_CONTROLS=== Error during reference refresh: {refresh_error}")
    
    def reset_chat(self):
        """Reset the chat conversation when starting a new game"""
        print("===MEDIA_CONTROLS=== Resetting chat for new game")
        
        # Clear conversation history and agent state
        self.agent_inputs = []
        self.conversation_id = None
        
        # Clear chat history UI
        if self.chat_history:
            self.chat_history.controls.clear()
            
            # Add a new welcome message
            self.chat_history.controls.append(
                ft.Container(
                    content=ft.Text(
                        "Hi! I'm the assistant for the hangman game. You can:\n" +
                        "• Type letters in the chat\n" +
                        "• Say 'I want to use voice input' to speak letters\n" +
                        "• Say 'I want to draw a letter' to draw letters\n\n" +
                        "Would you like to start a new game?",
                        color=ft.Colors.BLACK
                    ),
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=ft.border_radius.all(10),
                    padding=10,
                    width=300,
                    alignment=ft.alignment.center_left
                )
            )
            self.chat_history.update()
            
        # Make sure input is enabled
        self._set_input_state(disabled=False)
    
    # New voice-to-text functionality for chat
    def _toggle_voice_to_text(self, e):
        """Toggle voice recording for text input"""
        # Ensure we have valid references
        if not self.mic_button:
            self._refresh_chat_input_references()
            if not self.mic_button:
                return
        
        if self.is_recording_voice_for_chat:
            # Stop recording
            self._stop_voice_to_text_recording()
        else:
            # Start recording
            self._start_voice_to_text_recording()
    
    def _start_voice_to_text_recording(self):
        """Start recording voice for text input"""
        if self.is_recording_voice_for_chat:
            return
        
        self.is_recording_voice_for_chat = True
        # Change mic icon to indicate recording
        self.mic_button.icon = ft.Icons.MIC_OFF
        self.mic_button.bgcolor = ft.colors.RED_400
        self.mic_button.update()
        
        # Start voice recording in a separate thread to avoid blocking the UI
        Thread(target=self._voice_to_text_worker).start()
    
    def _stop_voice_to_text_recording(self):
        """Stop recording voice for text input"""
        self.is_recording_voice_for_chat = False
        # Reset mic button appearance
        self.mic_button.icon = ft.Icons.MIC
        self.mic_button.bgcolor = None
        self.mic_button.update()
    
    def _voice_to_text_worker(self):
        """Worker thread to handle voice recording and conversion to text"""
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                print("===MEDIA_CONTROLS=== Microphone initialized successfully")
                try:
                    # Adjust for ambient noise and listen
                    print("===MEDIA_CONTROLS=== Starting ambient noise adjustment...")
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    print("===MEDIA_CONTROLS=== Starting to listen for speech...")
                    audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
                    print("===MEDIA_CONTROLS=== Audio captured, processing...")
                    
                    # Use Google's speech recognition to convert to text
                    text = recognizer.recognize_google(audio, language="en-US").strip()
                    print(f"===MEDIA_CONTROLS=== Speech recognized: {text}")
                    
                    # Update the chat input field with the recognized text
                    if self.chat_input:
                        self.chat_input.value = text
                        self.chat_input.update()
                        print("===MEDIA_CONTROLS=== Chat input updated with recognized text")
                    
                except sr.UnknownValueError:
                    print("===MEDIA_CONTROLS=== Could not understand audio")
                except sr.RequestError as e:
                    print(f"===MEDIA_CONTROLS=== Speech recognition service error: {e}")
                except sr.WaitTimeoutError:
                    print("===MEDIA_CONTROLS=== Listening timed out")
                except Exception as e:
                    print(f"===MEDIA_CONTROLS=== Error during speech recognition: {e}")
                    
        except Exception as e:
            print(f"===MEDIA_CONTROLS=== Error initializing microphone: {e}")
            # This is likely where the PaMacCore error would be caught
            
        finally:
            # Always reset the recording state
            self.is_recording_voice_for_chat = False
            
            # Reset mic button appearance
            if self.mic_button:
                self.mic_button.icon = ft.Icons.MIC
                self.mic_button.bgcolor = None
                self.mic_button.update()
                print("===MEDIA_CONTROLS=== Mic button reset to normal state")
    
    def ensure_ui_synced_with_game(self):
        """Ensure that the UI is synchronized with active game state"""
        # Import globally defined game_panel
        import sys
        try:
            # Get the main module's global variables
            main_module = sys.modules.get('__main__')
            if main_module and hasattr(main_module, 'global_game_panel'):
                game_panel = main_module.global_game_panel
                if game_panel:
                    # Force UI update with current game state
                    print("===MEDIA_CONTROLS=== Forcing UI update to sync with game state")
                    game_panel.force_update()
                    return True
                else:
                    print("===MEDIA_CONTROLS=== global_game_panel is None, can't sync UI")
            else:
                print("===MEDIA_CONTROLS=== No global_game_panel found in main module")
        except Exception as e:
            print(f"===MEDIA_CONTROLS=== Error syncing UI with game state: {e}")
        return False
    
    def _refresh_chat_input_references(self):
        """Refresh references to chat input components to ensure they're functional"""
        try:
            print("===MEDIA_CONTROLS=== Attempting to refresh chat input references")
            
            # Check if chat_view exists and has the expected structure
            if not self.chat_view:
                print("===MEDIA_CONTROLS=== Chat view is None, cannot refresh references")
                return
                
            if not hasattr(self.chat_view, 'controls'):
                print("===MEDIA_CONTROLS=== Chat view has no controls attribute")
                return
                
            if len(self.chat_view.controls) == 0:
                print("===MEDIA_CONTROLS=== Chat view has no controls")
                return
            
            print(f"===MEDIA_CONTROLS=== Chat view has {len(self.chat_view.controls)} controls")
            
            # The chat_view is a Column with the input row as the last element
            # Structure should be: [Title, Chat History Container, Input Row]
            if len(self.chat_view.controls) >= 3:
                # Refresh chat_history reference (second element - the container)
                chat_container = self.chat_view.controls[1]  # Chat history container
                if hasattr(chat_container, 'content'):
                    self.chat_history = chat_container.content
                    print("===MEDIA_CONTROLS=== Refreshed chat_history reference")
                
                # Refresh input components (last element - the input row)
                input_row = self.chat_view.controls[-1]  # Last element should be the input row
                print(f"===MEDIA_CONTROLS=== Found input row: {type(input_row)}")
                
                if hasattr(input_row, 'controls') and len(input_row.controls) >= 3:
                    print(f"===MEDIA_CONTROLS=== Input row has {len(input_row.controls)} controls")
                    
                    # Verify the types before assigning
                    text_field = input_row.controls[0]
                    send_btn = input_row.controls[1] 
                    mic_btn = input_row.controls[2]
                    
                    print(f"===MEDIA_CONTROLS=== Control types: {type(text_field)}, {type(send_btn)}, {type(mic_btn)}")
                    
                    # Only update references if they are the expected types
                    if hasattr(text_field, 'value') and hasattr(text_field, 'disabled'):  # TextField-like
                        self.chat_input = text_field
                        print("===MEDIA_CONTROLS=== Updated chat_input reference")
                    
                    if hasattr(send_btn, 'disabled'):  # Button-like
                        self.send_button = send_btn
                        print("===MEDIA_CONTROLS=== Updated send_button reference")
                    
                    if hasattr(mic_btn, 'disabled'):  # Button-like  
                        self.mic_button = mic_btn
                        print("===MEDIA_CONTROLS=== Updated mic_button reference")
                    
                    # Ensure they're enabled
                    self._set_input_state(disabled=False)
                    print("===MEDIA_CONTROLS=== Successfully refreshed all chat references")
                else:
                    print(f"===MEDIA_CONTROLS=== Input row structure not as expected. Controls: {len(input_row.controls) if hasattr(input_row, 'controls') else 'no controls'}")
            else:
                print(f"===MEDIA_CONTROLS=== Chat view doesn't have enough controls: {len(self.chat_view.controls)}")
                
        except Exception as e:
            print(f"===MEDIA_CONTROLS=== Error refreshing chat input references: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback: try to keep current references working if they exist
            try:
                if self.chat_input and self.send_button and self.mic_button:
                    self._set_input_state(disabled=False)
                    print("===MEDIA_CONTROLS=== Used fallback to enable existing references")
            except Exception as fallback_error:
                print(f"===MEDIA_CONTROLS=== Fallback also failed: {fallback_error}")
