import streamlit as st
import fitness_tools
from fitness_tools.meals.meal_maker import MakeMeal
import pandas as pd
import numpy as np

# Food nutrition data per 100g
FOOD_DATA = {
    "Chicken Breast (skinless)": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6},
    "Ground Beef (lean)": {"calories": 250, "protein": 26, "carbs": 0, "fat": 15},
    "Salmon": {"calories": 206, "protein": 22, "carbs": 0, "fat": 13},
    "Tuna (canned)": {"calories": 116, "protein": 25, "carbs": 0, "fat": 1},
    "Turkey Breast": {"calories": 157, "protein": 29, "carbs": 0, "fat": 4},
    "Egg (whole)": {"calories": 143, "protein": 13, "carbs": 1, "fat": 10},
    "Egg Whites": {"calories": 52, "protein": 11, "carbs": 1, "fat": 0},
    "Greek Yogurt": {"calories": 59, "protein": 10, "carbs": 3.6, "fat": 0.4},
    "Cottage Cheese": {"calories": 98, "protein": 11, "carbs": 3.4, "fat": 4.3},
    "White Rice (cooked)": {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3},
    "Brown Rice (cooked)": {"calories": 112, "protein": 2.6, "carbs": 23, "fat": 0.9},
    "Quinoa (cooked)": {"calories": 120, "protein": 4.4, "carbs": 21, "fat": 1.9},
    "Oats": {"calories": 389, "protein": 16.9, "carbs": 66, "fat": 6.9},
    "Pasta (cooked)": {"calories": 158, "protein": 5.8, "carbs": 31, "fat": 0.9},
    "Sweet Potato (cooked)": {"calories": 86, "protein": 1.6, "carbs": 20, "fat": 0.1},
    "Potato (cooked)": {"calories": 86, "protein": 1.8, "carbs": 20, "fat": 0.1},
    "Bread (whole wheat)": {"calories": 247, "protein": 13, "carbs": 41, "fat": 3.4},
    "Broccoli": {"calories": 34, "protein": 2.8, "carbs": 7, "fat": 0.4},
    "Spinach": {"calories": 23, "protein": 2.9, "carbs": 3.6, "fat": 0.4},
    "Kale": {"calories": 49, "protein": 4.3, "carbs": 8.8, "fat": 0.9},
    "Mixed Vegetables": {"calories": 65, "protein": 2.6, "carbs": 13, "fat": 0.6},
    "Avocado": {"calories": 160, "protein": 2, "carbs": 8.5, "fat": 14.7},
    "Olive Oil": {"calories": 884, "protein": 0, "carbs": 0, "fat": 100},
    "Almonds": {"calories": 579, "protein": 21, "carbs": 22, "fat": 49},
    "Peanut Butter": {"calories": 588, "protein": 25, "carbs": 20, "fat": 50}
}

# Initialize session state to store user selections
if 'meal_data' not in st.session_state:
    st.session_state.meal_data = {}

if 'active_meal' not in st.session_state:
    st.session_state.active_meal = 0

if 'macro_data' not in st.session_state:
    st.session_state.macro_data = None


def calculate_portions(foods, protein_target, carbs_target, fat_target):
    """Calculate food portions to meet macro targets"""
    meal_items = []

    # Track remaining macros to allocate
    remaining_protein = protein_target
    remaining_carbs = carbs_target
    remaining_fat = fat_target

    # 1. First handle vegetables (usually fixed portions)
    for veg in foods['vegetables']:
        portion = 100  # Standard vegetable portion

        protein = FOOD_DATA[veg]["protein"] * portion / 100
        carbs = FOOD_DATA[veg]["carbs"] * portion / 100
        fat = FOOD_DATA[veg]["fat"] * portion / 100
        calories = FOOD_DATA[veg]["calories"] * portion / 100

        remaining_protein -= protein
        remaining_carbs -= carbs
        remaining_fat -= fat

        meal_items.append({
            "Food": veg,
            "Amount (g)": portion,
            "Calories": calories,
            "Protein (g)": protein,
            "Carbs (g)": carbs,
            "Fat (g)": fat
        })

    # 2. Allocate fats
    for fat_food in foods['fats']:
        fat_per_100g = FOOD_DATA[fat_food]["fat"]

        if fat_per_100g > 0:
            portion = min((remaining_fat * 100) / fat_per_100g, 30)  # Cap at 30g for fats
        else:
            portion = 15  # Default small portion

        protein = FOOD_DATA[fat_food]["protein"] * portion / 100
        carbs = FOOD_DATA[fat_food]["carbs"] * portion / 100
        fat = FOOD_DATA[fat_food]["fat"] * portion / 100
        calories = FOOD_DATA[fat_food]["calories"] * portion / 100

        remaining_protein -= protein
        remaining_carbs -= carbs
        remaining_fat -= fat

        meal_items.append({
            "Food": fat_food,
            "Amount (g)": round(portion),
            "Calories": round(calories),
            "Protein (g)": round(protein, 1),
            "Carbs (g)": round(carbs, 1),
            "Fat (g)": round(fat, 1)
        })

    # 3. Allocate carbs
    for carb_food in foods['carbs']:
        carbs_per_100g = FOOD_DATA[carb_food]["carbs"]

        if carbs_per_100g > 0:
            # Set reasonable portion range based on food type
            max_portion = 150 if carb_food in ["White Rice (cooked)", "Brown Rice (cooked)", "Pasta (cooked)"] else 100
            min_portion = 50

            # Calculate portion based on carb target
            raw_portion = (remaining_carbs * 100) / carbs_per_100g
            portion = max(min(raw_portion, max_portion), min_portion)
        else:
            portion = 50  # Default portion

        protein = FOOD_DATA[carb_food]["protein"] * portion / 100
        carbs = FOOD_DATA[carb_food]["carbs"] * portion / 100
        fat = FOOD_DATA[carb_food]["fat"] * portion / 100
        calories = FOOD_DATA[carb_food]["calories"] * portion / 100

        remaining_protein -= protein
        remaining_carbs -= carbs
        remaining_fat -= fat

        meal_items.append({
            "Food": carb_food,
            "Amount (g)": round(portion),
            "Calories": round(calories),
            "Protein (g)": round(protein, 1),
            "Carbs (g)": round(carbs, 1),
            "Fat (g)": round(fat, 1)
        })

    # 4. Allocate proteins
    if foods['proteins']:
        protein_per_food = remaining_protein / len(foods['proteins'])

        for protein_food in foods['proteins']:
            protein_per_100g = FOOD_DATA[protein_food]["protein"]

            if protein_per_100g > 0:
                # Calculate portion but set reasonable limits
                raw_portion = (protein_per_food * 100) / protein_per_100g

                # Special handling for different protein types
                max_portion = 200 if protein_food in ["Chicken Breast (skinless)", "Turkey Breast"] else 150
                min_portion = 30

                portion = max(min(raw_portion, max_portion), min_portion)
            else:
                portion = 100  # Default portion

            protein = FOOD_DATA[protein_food]["protein"] * portion / 100
            carbs = FOOD_DATA[protein_food]["carbs"] * portion / 100
            fat = FOOD_DATA[protein_food]["fat"] * portion / 100
            calories = FOOD_DATA[protein_food]["calories"] * portion / 100

            meal_items.append({
                "Food": protein_food,
                "Amount (g)": round(portion),
                "Calories": round(calories),
                "Protein (g)": round(protein, 1),
                "Carbs (g)": round(carbs, 1),
                "Fat (g)": round(fat, 1)
            })

    return meal_items


def calculate_macros(weight, goal, activity_level):
    """Calculate macros using MakeMeal with standard macro splits"""
    try:
        # Create MakeMeal object with required parameters
        meal_obj = MakeMeal(
            weight=weight,
            goal=goal,
            activity_level=activity_level,
            body_type=None,
            fat_percent=0.30,
            protein_percent=0.40,
            carb_percent=0.30
        )

        # Calculate all values
        min_cals = meal_obj.daily_min_calories()
        max_cals = meal_obj.daily_max_calories()
        avg_cals = (min_cals + max_cals) / 2

        min_protein = meal_obj.daily_min_protein()
        max_protein = meal_obj.daily_max_protein()
        avg_protein = (min_protein + max_protein) / 2

        min_carbs = meal_obj.daily_min_carbs()
        max_carbs = meal_obj.daily_max_carbs()
        avg_carbs = (min_carbs + max_carbs) / 2

        min_fat = meal_obj.daily_min_fat()
        max_fat = meal_obj.daily_max_fat()
        avg_fat = (min_fat + max_fat) / 2

        # Return the calculated data
        return {
            "calories": {
                "min": min_cals,
                "max": max_cals,
                "avg": avg_cals
            },
            "protein": {
                "min": min_protein,
                "max": max_protein,
                "avg": avg_protein
            },
            "carbs": {
                "min": min_carbs,
                "max": max_carbs,
                "avg": avg_carbs
            },
            "fat": {
                "min": min_fat,
                "max": max_fat,
                "avg": avg_fat
            }
        }
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None


def main():
    st.set_page_config(page_title="Complete Fitness Meal Planner", layout="wide")

    # App navigation
    st.sidebar.title("Fitness Meal Planner")
    app_mode = st.sidebar.radio("Select Mode", ["Calculate Macros", "Plan Meals"])

    if app_mode == "Calculate Macros":
        macro_calculator()
    else:
        meal_planner()


def macro_calculator():
    st.title("Macro Calculator")
    st.write("Please add your information on the sidebar")
    st.write("After filling the information please press **Calculate Macros**")
    st.write("The next step is pressing **Plan Meals**")

    # Create sidebar for inputs
    st.sidebar.header("Client Information")
    client_name = st.sidebar.text_input("Client Name", "")

    # Weight input (as integer since MakeMeal requires int)
    weight = int(
        st.sidebar.number_input("Current weight (lbs)", min_value=50.0, max_value=500.0, value=150.0, step=1.0))

    # Goal selection with display labels
    goal_options = ["weight_loss", "weight_gain", "maintenance"]
    goal_labels = ["Weight Loss", "Muscle Gain", "Maintenance"]

    goal_index = st.sidebar.selectbox(
        "Primary Goal",
        options=range(len(goal_options)),
        format_func=lambda i: goal_labels[i],
        index=0
    )
    goal = goal_options[goal_index]

    # Activity level selection with display labels
    activity_options = ["sedentary", "moderate", "very"]
    activity_labels = ["Sedentary", "Moderate", "Very Active"]

    activity_descriptions = {
        "Sedentary": "Little to no exercise",
        "Moderate": "Moderate exercise 1-2 days/week",
        "Very Active": "Hard exercise 3-7 days/week",
    }

    activity_index = st.sidebar.selectbox(
        "Activity Level",
        options=range(len(activity_options)),
        format_func=lambda i: activity_labels[i],
        index=2,
        help="\n".join([f"{k}: {v}" for k, v in activity_descriptions.items()])
    )
    activity_level = activity_options[activity_index]

    # Calculate macros on button click
    if st.sidebar.button("Calculate Macros"):
        with st.spinner("Calculating macros..."):
            # Calculate macros
            macro_data = calculate_macros(weight, goal, activity_level)

            if macro_data:
                # Store in session state for meal planning
                st.session_state.macro_data = macro_data
                st.session_state.client_info = {
                    "name": client_name,
                    "weight": weight,
                    "goal": goal,
                    "activity_level": activity_level
                }

                # Display user details
                st.header("Client Macro Calculation Results")

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Client Information")
                    if client_name:
                        st.write(f"**Client:** {client_name}")
                    st.write(f"**Weight:** {weight} lbs")
                    st.write(f"**Goal:** {goal.replace('_', ' ').title()}")
                    st.write(f"**Activity Level:** {activity_level.title()}")

                # Create a dataframe for displaying the macros
                macro_df = pd.DataFrame({
                    "Nutrient": ["Calories", "Protein", "Carbs", "Fat"],
                    "Minimum": [
                        f"{macro_data['calories']['min']} kcal",
                        f"{macro_data['protein']['min']}g",
                        f"{macro_data['carbs']['min']}g",
                        f"{macro_data['fat']['min']}g"
                    ],
                    "Maximum": [
                        f"{macro_data['calories']['max']} kcal",
                        f"{macro_data['protein']['max']}g",
                        f"{macro_data['carbs']['max']}g",
                        f"{macro_data['fat']['max']}g"
                    ],
                    "Target (Avg)": [
                        f"{macro_data['calories']['avg']:.0f} kcal",
                        f"{macro_data['protein']['avg']:.0f}g",
                        f"{macro_data['carbs']['avg']:.0f}g",
                        f"{macro_data['fat']['avg']:.0f}g"
                    ]
                })

                st.subheader("Daily Macronutrient Targets")
                st.table(macro_df)

                # Add export option
                st.download_button(
                    label="Export Macros as CSV",
                    data=macro_df.to_csv(index=False),
                    file_name=f"{'client_' + client_name if client_name else 'macros'}.csv",
                    mime="text/csv"
                )

                st.success(
                    "Macros calculated successfully! You can now go to the 'Plan Meals' tab to create a meal plan.")


def meal_planner():
    st.title("Meal Planner")

    # Check if macros have been calculated
    if st.session_state.macro_data is None:
        st.warning("Please calculate your macros first using the 'Calculate Macros' tab.")
        if st.button("Go to Macro Calculator"):
            st.session_state.app_mode = "Calculate Macros"
            st.experimental_rerun()
        return

    # Display macro information
    macro_data = st.session_state.macro_data
    client_info = st.session_state.client_info

    # Header with client info
    st.header(f"Meal Plan for {client_info['name'] if client_info['name'] else 'Client'}")
    st.subheader("Daily Targets")

    # Display daily targets in a nice layout
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Calories", f"{int(macro_data['calories']['avg'])} kcal")
    col2.metric("Protein", f"{int(macro_data['protein']['avg'])}g")
    col3.metric("Carbs", f"{int(macro_data['carbs']['avg'])}g")
    col4.metric("Fat", f"{int(macro_data['fat']['avg'])}g")

    # Number of meals
    num_meals = st.radio("Number of meals per day", [1, 2, 3, 4, 5, 6], horizontal=True, index=2)

    # Per-meal targets
    st.write("---")
    protein_per_meal = round(macro_data['protein']['avg'] / num_meals)
    carbs_per_meal = round(macro_data['carbs']['avg'] / num_meals)
    fat_per_meal = round(macro_data['fat']['avg'] / num_meals)
    calories_per_meal = round(macro_data['calories']['avg'] / num_meals)

    # Meal selector
    meal_tabs = st.tabs([f"Meal {i + 1}" for i in range(num_meals)])

    # Process each meal
    for meal_idx, meal_tab in enumerate(meal_tabs):
        with meal_tab:
            # Create key for this meal in session state if it doesn't exist
            meal_key = f"meal_{meal_idx}"
            if meal_key not in st.session_state.meal_data:
                st.session_state.meal_data[meal_key] = {
                    'proteins': [],
                    'carbs': [],
                    'vegetables': [],
                    'fats': []
                }

            # Display meal targets
            st.write(
                f"**Target**: {calories_per_meal} kcal, {protein_per_meal}g protein, {carbs_per_meal}g carbs, {fat_per_meal}g fat")

            # Food selection interface
            col1, col2 = st.columns(2)

            with col1:
                # Proteins
                st.subheader("Proteins")
                proteins = st.multiselect(
                    "Select proteins (1-2 items):",
                    options=list(FOOD_DATA.keys())[:9],  # First 9 items are proteins
                    default=st.session_state.meal_data[meal_key]['proteins'],
                    key=f"protein_select_{meal_idx}"
                )
                st.session_state.meal_data[meal_key]['proteins'] = proteins

                # Carbs
                st.subheader("Carbs")
                carbs = st.multiselect(
                    "Select carbs (1 item):",
                    options=list(FOOD_DATA.keys())[9:17],  # Items 9-16 are carbs
                    default=st.session_state.meal_data[meal_key]['carbs'],
                    key=f"carb_select_{meal_idx}"
                )
                st.session_state.meal_data[meal_key]['carbs'] = carbs

            with col2:
                # Vegetables
                st.subheader("Vegetables")
                vegetables = st.multiselect(
                    "Select vegetables (1-2 items):",
                    options=list(FOOD_DATA.keys())[17:21],  # Items 17-20 are vegetables
                    default=st.session_state.meal_data[meal_key]['vegetables'],
                    key=f"veg_select_{meal_idx}"
                )
                st.session_state.meal_data[meal_key]['vegetables'] = vegetables

                # Fats
                st.subheader("Fats")
                fats = st.multiselect(
                    "Select fats (0-1 item):",
                    options=list(FOOD_DATA.keys())[21:],  # Items 21+ are fats
                    default=st.session_state.meal_data[meal_key]['fats'],
                    key=f"fat_select_{meal_idx}"
                )
                st.session_state.meal_data[meal_key]['fats'] = fats

            # Calculate button
            if st.button("Calculate Portions", key=f"calc_btn_{meal_idx}"):
                # Validate selections
                missing_categories = []
                if not proteins:
                    missing_categories.append("protein")
                if not carbs:
                    missing_categories.append("carbs")
                if not vegetables:
                    missing_categories.append("vegetables")

                if missing_categories:
                    st.warning(
                        f"Please select at least one food for each of these categories: {', '.join(missing_categories)}")
                else:
                    # Calculate portions
                    meal_items = calculate_portions(
                        st.session_state.meal_data[meal_key],
                        protein_per_meal,
                        carbs_per_meal,
                        fat_per_meal
                    )

                    # Create DataFrame for display
                    meal_df = pd.DataFrame(meal_items)

                    # Calculate totals
                    totals = {
                        "Food": "TOTAL",
                        "Amount (g)": meal_df["Amount (g)"].sum(),
                        "Calories": round(meal_df["Calories"].sum()),
                        "Protein (g)": round(meal_df["Protein (g)"].sum(), 1),
                        "Carbs (g)": round(meal_df["Carbs (g)"].sum(), 1),
                        "Fat (g)": round(meal_df["Fat (g)"].sum(), 1)
                    }

                    # Add totals row to DataFrame
                    meal_df = pd.concat([meal_df, pd.DataFrame([totals])], ignore_index=True)
                    st.write("### Your Meal Plan")
                    st.dataframe(meal_df, use_container_width=True)

                    # Show comparison to targets
                    st.write("### Targets vs. Actual")
                    comparison = pd.DataFrame([
                        {"Nutrient": "Calories", "Target": calories_per_meal, "Actual": totals["Calories"],
                         "Difference": totals["Calories"] - calories_per_meal},
                        {"Nutrient": "Protein", "Target": protein_per_meal, "Actual": totals["Protein (g)"],
                         "Difference": totals["Protein (g)"] - protein_per_meal},
                        {"Nutrient": "Carbs", "Target": carbs_per_meal, "Actual": totals["Carbs (g)"],
                         "Difference": totals["Carbs (g)"] - carbs_per_meal},
                        {"Nutrient": "Fat", "Target": fat_per_meal, "Actual": totals["Fat (g)"],
                         "Difference": totals["Fat (g)"] - fat_per_meal}
                    ])
                    st.dataframe(comparison, use_container_width=True)

                    # Add usage notes
                    st.info("Remember to measure your portions accurately using a food scale for best results!")

                    # Add export option
                    st.download_button(
                        label=f"Export Meal {meal_idx + 1} as CSV",
                        data=meal_df.to_csv(index=False),
                        file_name=f"meal_{meal_idx + 1}_plan.csv",
                        mime="text/csv"
                    )


if __name__ == "__main__":
    main()