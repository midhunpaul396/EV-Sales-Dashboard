import openai
import pandas as pd
import streamlit as st
import google.generativeai as genai

# openai.api_key = st.secrets["OPENAI_API_KEY"]
gemini_api_key = st.secrets["GEMINI_API_KEY"]

# Streamlit UI setup
st.title("Chatbot")

# Initialize session state variables if not already initialized
if "total_revenue" not in st.session_state:
    df = pd.read_csv('Dataset.csv')
    # Key Performance Indicators (KPIs)
    total_revenue = round(df["Total Revenue"].sum(), 2)  # Total Revenue
    total_profit = round(df["Profit"].sum(), 2)  # Total Profit
    total_orders = df["Transaction ID"].nunique()  # Total Transactions
    average_sales_per_order = round(total_revenue / total_orders, 2) if total_orders > 0 else 0  # Avg Sales per Order
    average_profit_margin = round((df["Profit"].sum() / df["Total Revenue"].sum()) * 100, 2) if total_revenue > 0 else 0  # Profit Margin %
    average_revenue_per_transaction = round(df["Total Revenue"].mean(), 2)  # Avg Revenue per Transaction
    total_quantity_sold = df["Quantity Sold"].sum()  # Total Quantity Sold
    sales_per_customer = round(total_revenue / df['Customer ID'].nunique(), 2)  # Sales per Customer
    profit_by_category = (
    df.groupby("Product_Category")["Profit"]
    .sum()
    .reset_index()
    )

    # Store KPIs in session state
    st.session_state.total_revenue = total_revenue
    st.session_state.total_profit = total_profit
    st.session_state.average_profit_margin = average_profit_margin
    st.session_state.total_orders = total_orders
    st.session_state.average_sales_per_order = average_sales_per_order
    st.session_state.average_revenue_per_transaction = average_revenue_per_transaction
    st.session_state.total_quantity_sold = total_quantity_sold
    st.session_state.sales_per_customer = sales_per_customer
    st.session_state.profit_by_category = profit_by_category

# Define the data summary context
data_summary = (
    f"Filtered Data Summary:\n"
    f"Total Revenue: ${st.session_state.total_revenue:,}\n"
    f"Total Profit: ${st.session_state.total_profit:,}\n"
    f"Average Profit Margin: {st.session_state.average_profit_margin}%\n"
    f"Average Sales per Order: ${st.session_state.average_sales_per_order:,}\n"
    f"Average Revenue per Transaction: ${st.session_state.average_revenue_per_transaction:,}\n"
    f"Total Quantity Sold: {st.session_state.total_quantity_sold:,} units\n"
    f"Sales per Customer: ${st.session_state.sales_per_customer:,}\n"
    f"Total Unique Transactions: {st.session_state.total_orders}\n\n"
    f"Total Unique Transactions: {st.session_state.profit_by_category}\n\n"
    "You are an intelligent assistant that provides explanations about the key performance indicators (KPIs) and trends in sales and profit. "
    "You can also identify patterns, insights, and suggestions based on the given metrics and user queries. "
    "Ask me about sales trends, profit margins, customer behavior, product category performance, or anything else related to the dataset. "
    "I can provide insights to guide business decisions, optimize sales strategies, and improve overall performance."
) 

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Ask a question about the sales data:"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate assistant response using OpenAI or Gemini
    try:
        with st.chat_message("assistant"):
            if True:
                # Create the model with Gemini's configuration
                generation_config = {
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 550,
                    "response_mime_type": "text/plain",
                }

                model = genai.GenerativeModel(
                    model_name="gemini-1.5-pro",
                    generation_config=generation_config,
                    system_instruction="You are an intelligent assistant that provides explanations about the key performance indicators (KPIs) and trends in sales and profit.",
                )

                # Start chat with Gemini
                chat_session = model.start_chat(
                    history=[
                        {
                            "role": "user",
                            "parts": [
                                data_summary + "\n"
                            ],
                        },
                        {
                            "role": "user",
                            "parts": [
                                "Also, consider this prompt: " + prompt + "\n"
                            ],
                        },
                    ]
                )

                # Get response from Gemini (Ensure content is non-empty)
                assistant_response = chat_session.send_message("Reply to the prompt")

                # Extract the text from the response object
                assistant_response_text = assistant_response.text.strip()
                st.markdown(assistant_response_text)
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": assistant_response_text})

            else:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[ 
                        {"role": "system", "content": "You are an intelligent assistant that provides explanations about the key performance indicators (KPIs) and trends in sales and profit."},
                        {"role": "user", "content": data_summary},  # Include the data summary as context
                        {"role": "user", "content": prompt},  # User's input query
                    ],
                    max_tokens=550,
                    temperature=0.7,
                )

                # Extract and display assistant response
                assistant_response = response["choices"][0]["message"]["content"].strip()

                # Display the assistant's response
                st.markdown(assistant_response.strip())

                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": assistant_response.strip()})

    except Exception as e:
        st.error(f"Error generating response: {e}")
