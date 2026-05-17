import threading
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from plyer import filechooser
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
import os
import json
from backend.model import Gemma4Model


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
USER_DATA = os.path.join(DATA_DIR, "user_data.json")

# Home Screen UI
class HomeScreen(Screen):
    selected_files = []
    def open_menu(self):
        self.manager.current = "menu"
    def add_files(self):
        filechooser.open_file(
            title="Pick pdf or images",
            multiple=True,
            on_selection=self.selected_file
        )

    def selected_file(self, selection):
        if selection:
            self.selected_files = selection
            print("Selected files:", self.selected_files)

    # Chat options
    def first_suggestion(self):
        self.ids.user_input.text = "What are the most common health issues?"

    def second_suggestion(self):
        self.ids.user_input.text = "What foods should I avoid?"

    def third_suggestion(self):
        self.ids.user_input.text = "Suggest exercises for better heart health"

    def fourth_suggestion(self):
        self.ids.user_input.text = "What is LDL cholesterol?"
        
    def send_message(self):
        user_text = self.ids.user_input.text.strip()
        if not user_text:
            return


        self.ids.suggestion_buttons.opacity = 0
        self.ids.suggestion_buttons.disabled = True

        self.ids.suggestion_buttons.height = 0
        self.ids.suggestion_buttons.size_hint_y = None

        self.ids.img_logo.opacity = 0
        self.ids.img_logo.height = 0
        self.ids.img_logo.size_hint_y = None 

        self.ids.ai_response.opacity = 1
        self.ids.ai_response.disabled = False
        self.ids.user_message_box.clear_widgets()

        # USER MESSAGE 
        user_bubble = BoxLayout(
            orientation="vertical",
            size_hint=(0.7, None), 
            pos_hint={"right": 1}, 
            padding=15
        )

        user_bubble.bind(minimum_height=user_bubble.setter("height"))

        with user_bubble.canvas.before:
            Color(0.035, 0.007, 0.905, 1)
            user_bubble.rect = RoundedRectangle(radius=[20])

        def update_rect(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size

        user_bubble.bind(pos=update_rect, size=update_rect)

        user_label = Label(
            text=user_text,
            color=(1, 1, 1, 1),
            halign="right",
            size_hint_y=None,
            font_name="assets/NotoSans-VariableFont_wdth,wght.ttf"
        )

        user_label.bind(
            width=lambda s, w: setattr(s, 'text_size', (w, None)),
            texture_size=lambda s, t: setattr(s, 'height', t[1])
        )

        user_bubble.add_widget(user_label)
        self.ids.user_message_box.add_widget(user_bubble)
        self.current_user_message = user_text

        self.ids.scroll_content.clear_widgets()

        # AI RESPONSE
        self.response_label = Label(
        text="Analyzing........",
        size_hint_y=None,
        color=(1, 1, 1, 1),
        halign="center",
        valign="middle"
    )

        self.response_label.bind(
            width=lambda s, w: setattr(s, 'text_size', (w, None)),
            texture_size=lambda s, t: setattr(s, 'height', t[1])
        )
    
        self.ids.scroll_content.clear_widgets()
        self.ids.scroll_content.add_widget(self.response_label)
    
    
        self.loading_texts = [
            "Analyzing........",
            "Thinking.........",
            "Retrieving Relevant Information.........",
            "Preparing.........",
            "Checking Medical Context.........",
            "Reviewing Details.........",
            "Organizing Response.........",
            "Optimizing Answer.........",
            "Almost Ready.........",
        ]
    
        self.loading_index = 0
    
        self.loading_event = Clock.schedule_interval(
            self.change_loading_text, 5) # change the loading text after every 5 sec
    
        self.ids.user_input.text = ""
    
        threading.Thread(
            target=self.get_ai_response,
            daemon=True
        ).start()


    def change_loading_text(self, dt):

        self.loading_index += 1
        
        if self.loading_index >= len(self.loading_texts):
            self.loading_index = 0
        self.response_label.text = self.loading_texts[self.loading_index]


    def get_ai_response(self):
        try:
            user_text = self.current_user_message

            base_dir = os.path.dirname(__file__)
            file_path = os.path.join(base_dir, "data", "user_data.json")

            with open(file_path, "r") as file:
                user_data = json.load(file)

        except (FileNotFoundError, json.JSONDecodeError):
            user_data = {}

        try:
            name = user_data.get('name')
            USER_NAME = name if name else "NOT PROVIDED"

            age = user_data.get('age')
            USER_AGE = age if age else "NOT PROVIDED"

            gender = user_data.get('gender')
            USER_GENDER = gender if gender else "NOT PROVIDED"

            # Add user's name, age, gender with question for better response
            PROMPT = f"""
USER NAME: {USER_NAME}
USER's AGE: {USER_AGE}
USER's GENDER: {USER_GENDER}

USER's QUESTION: {user_text}
"""

            model = Gemma4Model(
                prompt=PROMPT,
                files=self.selected_files
            )

            ai_response = model.answer()

            Clock.schedule_once(
                lambda dt: self.show_ai_response(ai_response)
            )

        except Exception as e:
            print(e)

            Clock.schedule_once(
            lambda dt, err=str(e):
            self.show_ai_response(f"Error: {err}")
            )

    def show_ai_response(self, ai_text):

        self.loading_event.cancel()

        try:
            data = json.loads(ai_text)

            # check the type of response
            response_type = data.get("type")

            self.ids.scroll_content.clear_widgets()

            if response_type == "chat":
                self.show_chat_response(data)

            elif response_type == "report_analyse":
                self.show_report_analysis(data)

            elif response_type == "plan_lifestyle":
                self.show_lifestyle_plan(data)

            else:
                self.show_error("Unknown response type")

        except Exception as e:
            print(e)


    # NORMAL CHATTING UI
    def show_chat_response(self, data):

        response = data.get("response", "")
        
        label = Label(
            text=response,
            color=(1,1,1,1),
            size_hint_y=None,
            halign="left",
            valign="top",
            font_name="assets/NotoSans-VariableFont_wdth,wght.ttf"
        )

        label.bind(
            width=lambda s,w: setattr(s, "text_size", (w, None)),
            texture_size=lambda s,t: setattr(s, "height", t[1])
        )

        self.ids.scroll_content.add_widget(label)

    # MEDICAL REPORT ANALYSIS UI
    def show_report_analysis(self, data):

        summary = data.get("health_summary", "")
        good = data.get("good_indicators", "")
        maintain = data.get("how_to_maintain", "")
        bad = data.get("bad_indicators", "")
        improve = data.get("how_to_improve", "")
        important_terms = data.get("important_terms", "")
        risk_level = data.get("risk_level", "")
        notes = data.get("notes", "")

        container = BoxLayout(
            orientation="vertical",
            spacing=20,
            size_hint_y=None,
            padding=20
        )
        
        with container.canvas.before:
                    Color(0,0,0, 1)
                    container.rect = RoundedRectangle(radius=[15])

        def update_rect(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size

        container.bind(pos=update_rect, size=update_rect, minimum_height=container.setter("height"))


        title = Label(
            text="AI Health Analysis",
            font_size=28,
            bold=True,
            color=(0,1,0,1),
            size_hint_y=None,
            height=60
        )

        container.add_widget(title)

        summary_card = self.create_card(
            "Health Summary",
            summary,
            (0, 0.76, 1, 1)
        )

        good_card = self.create_card(
            "Good Indicators",
            good,
            (0.13, 0.77, 0.37, 1)
        )

        maintain_card = self.create_card(
            "How to Maintain",
            maintain,
            (0.08, 0.39, 0.2, 1)
        )

        bad_card = self.create_card(
            "Needs Attention",
            bad,
            (0.96, 0.62, 0.04, 1)
        )

        improve_card = self.create_card(
            "How To Improve",
            improve,
            (0.92, 0.7, 0.03, 1)
        )

        important_terms_card = self.create_card(
            "Important Terms",
            important_terms,
            (0.66, 0.33, 0.97, 1)
        )

        risk_level_card = self.create_card(
            "Overall Risk Level",
            risk_level,
            (0.98, 0.44, 0.52, 1)
        )

        notes_card = self.create_card(
            "Notes",
            notes,
            (0.5, 0.55, 0.97, 1)
        )


        container.add_widget(summary_card)
        container.add_widget(good_card)
        container.add_widget(maintain_card)
        container.add_widget(bad_card)
        container.add_widget(improve_card)
        container.add_widget(important_terms_card)
        container.add_widget(risk_level_card)
        container.add_widget(notes_card)

        self.ids.scroll_content.add_widget(container)

    # LIFESTYLE PLANNER UI
    def show_lifestyle_plan(self, data):
        
        health_goal = data.get("health_goal", "")
        sleep = data.get("sleep", "")
        hydration = data.get("hydration", "")
        stress_management = data.get("stress_management", "")
        daily_habits = data.get("daily_habits", "")
        notes = data.get("notes", "")
        workout = data.get("workout", "")
        diet = data.get("diet", "")
        avoid = data.get("avoid", "")

        container = BoxLayout(
            orientation="vertical",
            spacing=20,
            size_hint_y=None,
            padding=20
        )

        with container.canvas.before:
            Color(0,0,0, 1)
            container.rect = RoundedRectangle(radius=[15])

        def update_rect(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size

        container.bind(pos=update_rect, size=update_rect, minimum_height=container.setter("height"))

        title = Label(
            text="Personalized Health Plan",
            font_size=28,
            color=(1,1,1, 1),
            size_hint_y=None,
            height=60
        )

        container.add_widget(title)

        goal_card = self.create_card(
            "Health Goal",
            health_goal,
            (0.48, 0.18, 0.97, 1),
        )
        diet_card = self.create_card(
            "Diet Plan",
            diet,
            (0.43, 0.16, 0.85, 1),
        )

        workout_card = self.create_card(
            "Workout",
            workout,
            (0.98, 0.34, 0.03, 1),
        )

        avoid_card = self.create_card(
            "Things To Avoid",
            avoid,
            (0.94, 0.28, 0.44, 1),
        )

        sleep_card = self.create_card(
            "Sleep",
            sleep,
            (0.22, 0.52, 1, 1),
        )

        hydration_card = self.create_card(
            "Hydration",
            hydration,
            (0, 0.76, 1, 1),
        )

        stress_management_card = self.create_card(
            "Stress Management",
            stress_management,
            (0.62, 0.31, 0.87, 1),
        )

        daily_habits_card = self.create_card(
            "Daily Habits",
            daily_habits,
            (0.22, 0.83, 0.62, 1),
        )

        notes_card = self.create_card(
            "Notes",
            notes,
            (1, 0.72, 0.01, 1),
        )

        
        container.add_widget(goal_card)
        container.add_widget(diet_card)
        container.add_widget(workout_card)
        container.add_widget(sleep_card)
        container.add_widget(hydration_card)
        container.add_widget(stress_management_card)
        container.add_widget(daily_habits_card)
        container.add_widget(avoid_card)
        container.add_widget(notes_card)

        self.ids.scroll_content.add_widget(container)

    def create_card(self, title_text, body_text, bg_color):

        card = BoxLayout(
            orientation="vertical",
            padding=20,
            spacing=10,
            size_hint_y=None
        )

        card.bind(minimum_height=card.setter("height"))

        with card.canvas.before:
            Color(*bg_color)
            card.rect = RoundedRectangle(radius=[25])

        def update_rect(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size

        card.bind(pos=update_rect, size=update_rect)

        title = Label(
            text=title_text,
            bold=True,
            font_size=22,
            color=(1,1,1,1),
            size_hint_y=None,
            height=40
        )

        body = Label(
            text=body_text,
            color=(1,1,1,1),
            halign="left",
            valign="top",
            size_hint_y=None,
            font_name="assets/NotoSans-VariableFont_wdth,wght.ttf"
        )

        body.bind(
            width=lambda s,w: setattr(s, "text_size", (w-40, None)),
            texture_size=lambda s,t: setattr(s, "height", t[1])
        )

        card.add_widget(title)
        card.add_widget(body)

        return card
    
# Menu
class MenuScreen(Screen):
    def back(self, instance):
        self.manager.current = "home"
    
    def privacy_section(self):
        self.manager.current = "privacy_section"

    def change_to_settings(self):
        self.manager.current = "settings"

    def guide_screen(self):
        self.manager.current = "guide_screen"

# Privacy section
class PrivacyScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.ids.privacy_label.text = """    

[b]Your health data belongs to you.[/b]

Your medical information is only used to help the AI understand your reports and provide simpler explanations and personalized health suggestions.


[size=24][b]How Your Data Is Used[/b][/size]

When you upload reports like:

• Blood tests  
• CBC reports  
• MRI scans  
• CT scans  
• Ultrasounds  
• Other medical records  

[b]The information goes directly to the AI system for processing.[/b]

The AI analyzes the report, summarizes it in simple language, and may provide personalized lifestyle suggestions based on your medical history, such as:

• Diet recommendations  
• Sleep guidance  
• Exercise suggestions  
• Daily routine improvements  
• Healthy lifestyle habits  


[size=24][b]Data Protection[/b][/size]

[b]We do not share, sell, or give your medical data to advertisers, companies, or unrelated third parties.[/b]

Your uploaded reports are only used for:

• Providing HealthMate features  
• Generating health explanations  
• Creating personalized suggestions  
• Improving your understanding of health information  


[size=24][b]Important Note[/b][/size]

HealthMate is an educational AI assistant and not a replacement for professional medical advice, diagnosis, or treatment.

Always consult a qualified healthcare professional for serious medical concerns or emergencies.
"""

    def back(self, instance):
        self.manager.current = "menu"

# Settings section
class Settings(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def on_enter(self):

        try:
            base_dir  = os.path.dirname(__file__)
            file_path = os.path.join(base_dir, "data", "user_data.json")


            with open(file_path, "r") as file:
                user_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            user_data = {}

        if "name" in user_data:
            self.ids.user_name.text = f"Name: {user_data['name']}"
            self.ids.user_name.color = (0,1,0,1)
        if "age" in user_data:
            self.ids.user_age.text = f"Age: {user_data['age']}"
            self.ids.user_age.color = (0,1,0,1)
        if "gender" in user_data:
            self.ids.user_gender.text = f"Gender: {user_data['gender']}"
            self.ids.user_gender.color = (0,1,0,1)

    def change_user_details(self):
        edited_name = self.ids.edited_user_name.text.strip()
        edited_age = self.ids.edited_user_age.text.strip()
        edited_gender = self.ids.edited_user_gender.text.strip()
        edited_details_label = self.ids.new_user_details

        if not edited_name and not edited_age and not edited_gender:
            edited_details_label.text = "Please enter valid details."
            edited_details_label.color = (1,0,0,1)
            return
        try:
            
            base_dir  = os.path.dirname(__file__)
            file_path = os.path.join(base_dir, "data", "user_data.json")


            with open(file_path, "r") as file:
                user_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            user_data = {}

        if edited_name:
            user_data['name'] = edited_name
            edited_details_label.text = "Your details are updated successfully. Please restart the app to see the latest details."
            edited_details_label.color = (0,1,0,1)
        if edited_age:
            user_data['age'] = edited_age
            edited_details_label.text = "Your details are updated successfully. Please restart the app to see the latest details."
            edited_details_label.color = (0,1,0,1)
        if edited_gender:
            user_data['gender'] = edited_gender
            edited_details_label.text = "Your details are updated successfully. Please restart the app to see the latest details."
            edited_details_label.color = (0,1,0,1)
        with open(file_path, "w") as file:
            json.dump(user_data, file, indent=4)


    def back(self, instance):
        self.manager.current = "menu"

# How to use section
class GuideScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.ids.guide_label.text = """
HealthMate is your [b]AI-powered health assistant[/b] designed to help you understand medical reports, ask health-related questions, and create healthier lifestyle habits using simple and easy-to-understand language.

Whether you upload a [b]blood test[/b], [b]MRI[/b], [b]CT scan[/b], [b]ultrasound[/b], or ask a medical question, HealthMate helps explain things clearly and provides personalized health guidance.


[size=24][b]Upload Your Medical Report[/b][/size]

Tap the [b]Upload Report[/b] button on the home screen.

You can upload:

• PDF medical reports  
• Blood test reports  
• MRI reports  
• CT scan reports  
• Ultrasound reports  
• Medical report images  

HealthMate will securely process your report and extract important medical information.


[size=24][b]Get Your Report Explained[/b][/size]

After uploading the report, HealthMate analyzes it using AI and generates a simple explanation of your health report.

The app can:

• Explain difficult medical terms in simple words  
• Highlight healthy indicators  
• Detect values that may need attention  
• Explain what those values mean  
• Suggest ways to improve unhealthy indicators  

This helps users understand their reports without needing medical knowledge.


[size=24][b]Ask Medical Questions[/b][/size]

You can ask HealthMate health-related questions just like chatting with an assistant.

[b]Example questions:[/b]

• “What does LDL cholesterol mean?”  
• “How can I increase hemoglobin?”  
• “What foods help reduce blood sugar?”  
• “Is my blood pressure normal?”  
• “What causes Vitamin D deficiency?”  

HealthMate answers using simple and beginner-friendly language.


[size=24][b]Create a Healthy Lifestyle Plan[/b][/size]

HealthMate can generate a personalized lifestyle plan based on:

• Your medical reports  
• Health conditions  
• Medical history  
• Health goals  

The lifestyle planner may include:

• Healthy diet suggestions  
• Foods to avoid  
• Exercise recommendations  
• Sleep improvement tips  
• Hydration guidance  
• Daily routine planning  
• Stress management suggestions  

This helps users build healthier long-term habits.


[size=24][b]View Health Insights[/b][/size]

HealthMate organizes your results into easy-to-understand sections such as:

• Health Summary  
• Good Indicators  
• Indicators That Need Attention  
• Lifestyle Recommendations  
• Risk Level  

This makes health information simpler and more organized.


[size=24][b]Privacy & Safety[/b][/size]

Your medical information is sensitive and important.

HealthMate is designed with a [b]privacy-focused AI system[/b] to help protect user data.

[b]Important:[/b]

HealthMate is an educational AI assistant and [b]not[/b] a replacement for professional medical advice.

Always consult a healthcare professional for diagnosis, treatment, or emergencies.
"""

    def back(self, instance):
        self.manager.current = "menu"


class HealthMate(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(PrivacyScreen(name="privacy_section"))
        sm.add_widget(Settings(name="settings"))
        sm.add_widget(GuideScreen(name="guide_screen"))
        return sm

# RUN THE APP
if __name__ == "__main__":
    HealthMate().run()