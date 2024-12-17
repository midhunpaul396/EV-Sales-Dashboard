import streamlit as st
import pandas as pd
import google.generativeai as genai

# Load the CSV file
file_path = "Promotion.csv"


gemini_api_key = st.secrets["GEMINI_API_KEY"]

# Read the CSV file into a DataFrame
def load_data():
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        st.write("File not found, creating a new file.")
        return pd.DataFrame(columns=['Product Name', 'Product_Category', 'Description', 'Tagline', 'Price'])

# Function to save changes to the CSV file
def save_data(df):
    df.to_csv(file_path, index=False)
    st.success("Data has been updated successfully.")

# Load the data
df = load_data()

# Display the data table
st.subheader("Product Promotion Details")
st.write(df)


# Assuming df is your existing DataFrame
# Create the form for creating a new product
operation = st.radio("Choose Operation", ('Update Product', 'Create New Product'))

with st.form(key='product_form'):
    if operation == 'Update Product':
        # Select the product to update
        product_name = st.selectbox("Select Product to Update", df['Product Name'])

        # Find the selected product details
        selected_product = df[df['Product Name'] == product_name].iloc[0]

        # Create the form to update product details
        new_product_name = st.text_input("Product Name", value=selected_product['Product Name'])
        new_description = st.text_area("Description", value=selected_product['Description'])
        new_tagline = st.text_input("Tagline", value=selected_product['Tagline'])
        
        # Convert 'Price' to float before passing to the number input
        new_price = st.number_input(
            "Price", 
            value=float(selected_product['Price']) if isinstance(selected_product['Price'], (int, float)) else 0.0, 
            min_value=0.0
        )

    elif operation == 'Create New Product':
        # Create the form for a new product
        new_product_name = st.text_input("Product Name")
        new_description = st.text_area("Description")
        new_category = st.text_input("Product_Category")
        new_tagline = st.text_input("Tagline")
        new_price = st.number_input("Price", value=0.0, min_value=0.0)

    # Submit button inside the form
    submit_button = st.form_submit_button(label="Submit")

    if submit_button:
        if operation == 'Update Product':
            # Update the product in the dataframe
            df.loc[df['Product Name'] == product_name, 'Product Name'] = new_product_name
            df.loc[df['Product Name'] == new_product_name, 'Description'] = new_description
            df.loc[df['Product Name'] == new_product_name, 'Tagline'] = new_tagline
            df.loc[df['Product Name'] == new_product_name, 'Price'] = new_price
            
            # Save the updated dataframe to the CSV
            save_data(df)
            
            # Show the updated data table
            st.write("### Updated Product Promotion Details, reload to view the updated table")

        elif operation == 'Create New Product':
            # Add the new product to the dataframe
            new_product = {
                'Product Name': new_product_name,
                'Product_Category': new_category,  # You can prompt the user for the category if needed
                'Description': new_description,
                'Tagline': new_tagline,
                'Price': new_price
            }

            # Convert the new product dictionary to a DataFrame and concatenate it
            new_product_df = pd.DataFrame([new_product])
            df = pd.concat([df, new_product_df], ignore_index=True)

            # Save the updated dataframe to the CSV
            save_data(df)

            # Show the updated data table
            st.write("### Product Created Successfully, reload to see the updated table")

# Ensure 'product_performance' exists in session state
if 'product_performance' in st.session_state:
    product_performance = st.session_state.product_performance

    # filter and display High Performing products
    high_performing_products = product_performance[product_performance["Performance"] == "High Performing"]
    st.write("### High Performing Products")
    st.write(high_performing_products)
    high_performing_products = high_performing_products.merge(df, on="Product Name", how="left")

    # display Low Performing products
    low_performing_products = product_performance[product_performance["Performance"] == "Low Performing"]
    st.write("### Low Performing Products")
    st.write(low_performing_products)
    low_performing_products = low_performing_products.merge(df, on="Product Name", how="left")
else:
    df_selection = pd.read_csv('Dataset.csv')
    product_performance = (
        df_selection.groupby("Product Name")["Total Revenue"]
        .sum()
        .reset_index()
    )

    # Define a threshold for classification
    threshold = product_performance["Total Revenue"].median()

    # Classify products into "Low Performing" and "High Performing"
    product_performance["Performance"] = product_performance["Total Revenue"].apply(
        lambda x: "High Performing" if x > threshold else "Low Performing"
    )

    # Save to session state
    st.session_state.product_performance = product_performance
    product_performance = st.session_state.product_performance

    # filter and display High Performing products
    high_performing_products = product_performance[product_performance["Performance"] == "High Performing"]
    st.write("### High Performing Products")
    st.write(high_performing_products)
    high_performing_products = high_performing_products.merge(df, on="Product Name", how="left")

    # display Low Performing products
    low_performing_products = product_performance[product_performance["Performance"] == "Low Performing"]
    st.write("### Low Performing Products")
    st.write(low_performing_products)
    low_performing_products = low_performing_products.merge(df, on="Product Name", how="left")

    

# Gemini API integration for promotions
def generate_promotion(content_type, product_data):
    if gemini_api_key:  # If Gemini API key exists, use Gemini
        try:
            # Configure Gemini API
            genai.configure(api_key=gemini_api_key)
            generation_config = {
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            }

            # Create model with Gemini
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config=generation_config,
                system_instruction="You are an expert marketing assistant. Your goal is to create promotional content based on provided product details.",
            )

            # Create prompt for Gemini
            prompt = f"Create a one paragraph {content_type} for the following product:\n\n"
            prompt += f"Product Name: {product_data['Product Name']}\n"
            prompt += f"Description: {product_data['Description']}\n"
            prompt += f"Tagline: {product_data['Tagline']}\n"
            prompt += f"Price: {product_data['Price']}\n"

            # Start chat session
            chat_session = model.start_chat(
                history=[{"role": "user", "parts": [prompt]}]
            )

            # Generate promotion content using Gemini
            response = chat_session.send_message(prompt)

            st.session_state["gemini_promotion"] = response.text

            # Display generated promotion content
            st.subheader(f"Here is your {content_type} for {product_data['Product Name']}")
            st.write(response.text)

        except Exception as e:
            st.error(f"Gemini Free Quota Exceeded, Sorry. Try again after some time.")

# Button to trigger Social Media Promotion for Low Performing Products
if st.button("Generate Social Media Promotion (Low Performing Products)"):
    for _, product in low_performing_products.iterrows():
        generate_promotion("Social Media Promotion Text", product)

# Button to trigger Social Media Promotion for High Performing Products
if st.button("Generate Social Media Promotion (High Performing Products)"):
    for _, product in high_performing_products.iterrows():
        generate_promotion("Social Media Promotion Text", product)


