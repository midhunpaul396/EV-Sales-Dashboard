import google.generativeai as genai
import pandas as pd
import plotly.express as px
import streamlit as st
import openai
from fpdf import FPDF
import base64


# Fetch the OpenAI API key
# openai.api_key = st.secrets["OPENAI_API_KEY"]
gemini_api_key = st.secrets["GEMINI_API_KEY"]  # Fetch Gemini API key

# Set Streamlit page configuration
# st.set_page_config(page_title="AI Sales Dashboard", page_icon=":bar_chart:", layout="wide")

# Load the dataset
df = pd.read_csv('Dataset.csv')

df["Date"] = pd.to_datetime(df["Date"])

# Sidebar filters
st.sidebar.header("Please Filter Here:")


# Check if filters are in session state; if not, initialize them
if "Region" not in st.session_state:
    st.session_state.Region = df["Region"].unique()
if "Product_Category" not in st.session_state:
    st.session_state.Product_Category = df["Product_Category"].unique()
# if "Ship_Mode" not in st.session_state:
#     st.session_state.Ship_Mode = df["Ship_Mode"].unique()

def regionCallback():
    st.session_state.Region = st.session_state.RegKey
def ProCallback():
    st.session_state.Product_Category = st.session_state.ProKey
# def shipModeCallback():
#     st.session_state.Ship_Mode = st.session_state.ShipKey


# Sidebar multiselect filters using session state

Region = st.sidebar.multiselect(
    "Select the Region:",
    options=df["Region"].unique(),
    default=st.session_state.Region,
    on_change=regionCallback,
    key = 'RegKey'
)
Product_Category = st.sidebar.multiselect(
    "Select the Category:",
    options=df["Product_Category"].unique(),
    default=st.session_state.Product_Category,
    on_change=ProCallback,
    key = 'ProKey'

)



# Update session state with the latest filter values
st.session_state.Region = Region
st.session_state.Segment = Product_Category
# st.session_state.Ship_Mode = Ship_Mode

# Data selection based on filters
df_selection = df.query(
    "Region == @Region & Product_Category == @Product_Category"
)

product_performance = (
    df_selection.groupby("Product Name")["Total Revenue"]
    .sum()
    .reset_index()
)

profit_by_category = (
    df_selection.groupby("Product_Category")["Profit"]
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

if df_selection.empty:
    st.warning("No data available based on the current filter settings!")
    st.stop()

# ---- MAIN PAGE ----s
st.header(":bar_chart: EV Sales Dashboard")
st.markdown("### Key Metrics")

# --- KEY PERFORMANCE INDICATORS (KPIs) ---
total_revenue = round(df_selection["Total Revenue"].sum(), 2)  # Total Revenue
total_profit = round(df_selection["Profit"].sum(), 2)  # Total Profit
total_orders = df_selection["Transaction ID"].nunique()  # Total Transactions
average_sales_per_order = round(total_revenue / total_orders, 2) if total_orders > 0 else 0  # Avg Sales per Order
average_profit_margin = round((df_selection["Profit"].sum() / df_selection["Total Revenue"].sum()) * 100, 2) if total_revenue > 0 else 0  # Profit Margin %
average_revenue_per_transaction = round(df["Total Revenue"].mean(), 2)  # Avg Revenue per Transaction
total_quantity_sold = df_selection["Quantity Sold"].sum()  # Total Quantity Sold
sales_per_customer = round(total_revenue / df_selection['Customer ID'].nunique(), 2)  # Sales per Customer



# --- STORE KPIs IN SESSION STATE ---
st.session_state.total_revenue = total_revenue
st.session_state.total_profit = total_profit
st.session_state.average_profit_margin = average_profit_margin
st.session_state.average_revenue_per_transaction = average_revenue_per_transaction
st.session_state.total_orders = total_orders
st.session_state.average_profit_margin = average_profit_margin
st.session_state.total_quantity_sold = total_quantity_sold
st.session_state.sales_per_customer = sales_per_customer
st.session_state.average_sales_per_order = average_sales_per_order
st.session_state.profit_by_category = profit_by_category

# Displaying KPIs
left_column, middle_column, right_column = st.columns(3)
with left_column:
    st.markdown(f"### Total Revenue\n**${total_revenue:,}**")
with middle_column:
    st.markdown(f"### Total Profit\n**${total_profit:,}**")
with right_column:
    st.markdown(f"### Avg Sales/Order\n**${average_sales_per_order:,}**")

st.markdown("---")

# --- Sales and Profit by Product Category ---
sales_profit_by_category = (
    df_selection.groupby(by=["Product_Category"])[["Total Revenue", "Profit"]]
    .sum()
    .reset_index()
)

fig_sales_profit_bar = px.bar(
    sales_profit_by_category,
    x="Product_Category",
    y=["Total Revenue", "Profit"],
    title="Sales and Profit by Product Category",
    barmode="group",
    color_discrete_map={
        "Total Revenue": "royalblue",
        "Profit": "orange"
    },
    labels={"value": "Amount ($)", "variable": "Metrics"}
)

# Update the x-axis label to "Product Category"
fig_sales_profit_bar.update_layout(
    xaxis_title="Product Category"
)

st.plotly_chart(fig_sales_profit_bar, use_container_width=True)

# Revenue and Profit by Region
revenue_profit_by_region = (
    df_selection.groupby("Region")[["Total Revenue", "Profit"]]
    .sum()
    .reset_index()
)

fig_region = px.bar(
    revenue_profit_by_region,
    x="Region",
    y=["Total Revenue", "Profit"],
    title="Total Revenue and Profit by Region",
    barmode="group",
    text_auto=True
)
st.plotly_chart(fig_region, use_container_width=True)

# Top 5 Products by Total Revenue
top_products = (
    df_selection.groupby("Product Name")["Total Revenue"]
    .sum()
    .reset_index()
    .sort_values(by="Total Revenue", ascending=False)
    .head(5)
)

fig_top_products = px.bar(
    top_products,
    x="Total Revenue",
    y="Product Name",
    orientation="h",
    title="Top 5 Products by Total Revenue",
    text_auto=True
)
st.plotly_chart(fig_top_products, use_container_width=True)

# Convert Date to datetime if needed
df_selection["Date"] = pd.to_datetime(df_selection["Date"])

# Revenue Trend Over Time
revenue_trend = (
    df_selection.groupby("Date")["Total Revenue"]
    .sum()
    .reset_index()
)

fig_trend = px.line(
    revenue_trend,
    x="Date",
    y="Total Revenue",
    title="Revenue Trend Over Time"
)
st.plotly_chart(fig_trend, use_container_width=True)


# Region-Wise Product Performance Heatmap
product_region_pivot = df_selection.pivot_table(
    index="Product Name",
    columns="Region",
    values="Total Revenue",
    aggfunc="sum"
)

fig_heatmap = px.imshow(
    product_region_pivot,
    title="Product Performance by Region (Revenue)",
    labels=dict(x="Region", y="Product Name", color="Revenue")
)
st.plotly_chart(fig_heatmap, use_container_width=True)


# ---- AI-GENERATED INSIGHTS ----
st.markdown("### AI-Generated Insights")

# Enhanced prompt with more context
data_summary = (
    f"Dataset contains {len(df_selection)} records after filtering.\n"
    f"Total Revenue: ${total_revenue:,}\n"
    f"Total Profit: ${total_profit:,}\n"
    f"Average Sales per Order: ${average_sales_per_order:,}\n"
    f"Total Quantity Sold: {total_quantity_sold:,} units\n"
    f"Average Profit Margin: {average_profit_margin}%\n"
    f"Sales per Customer: ${sales_per_customer:,}\n"
    f"Number of Unique Customers: {df_selection['Customer ID'].nunique()}\n\n"
    f"Please analyze this data for potential patterns, identify anomalies or outliers, and provide actionable insights "
    f"that can help optimize sales and profits. Highlight any trends in sales by product category or region. "
    f"Consider analyzing the relationship between region, sales, and profit margins for further opportunities "
    f"to optimize pricing strategies. Identify any trends related to customer purchasing behaviors, such as repeat buyers "
)

# Button to trigger insights generation
if st.button("Generate Insights"):
    with st.spinner("Generating insights..."):
        if gemini_api_key:  # Check if the OpenAI API key is missing
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
                        system_instruction="You are an expert data analyst. Your goal is to provide insights from KPI's generated from a dataset's analysis.",
                    )

                    # Start chat session
                    chat_session = model.start_chat(
                        history=[
                            {"role": "user", "parts": [data_summary]},
                        ]
                    )

                    # Generate insights using Gemini
                    response = chat_session.send_message(data_summary)

                    st.session_state["gemini_insights"] = response.text

                    # Display Gemini insights
                    st.subheader("AI-Generated Insights")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Error generating insights with Gemini: {e}")
            else:
                st.error("Sorry, I am out of API fuel for both OpenAI and Gemini.")
        else:
            try:
                # Get OpenAI insights if the API key exists
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": "You are an expert data analyst."},
                              {"role": "user", "content": data_summary}],
                    max_tokens=600,
                    temperature=0.7,
                )

                # Extract and display OpenAI insights
                ai_insights = response["choices"][0]["message"]["content"].strip()
                st.subheader("AI-Generated Insights")
                st.write(ai_insights)

            except Exception as e:
                st.error(f"Error generating insights with OpenAI: {e}")
# Function to generate a PDF report
def generate_pdf_report(kpis, visualizations, gemini_insights):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Title
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(200, 10, txt="EV Sales Dashboard Report", ln=True, align="C")
    pdf.ln(10)

    # KPIs
    pdf.set_font("Arial", style="B", size=14)
    pdf.cell(200, 10, txt="Key Metrics", ln=True)
    pdf.set_font("Arial", size=12)
    for kpi, value in kpis.items():
        pdf.cell(200, 10, txt=f"{kpi}: {value}", ln=True)

    pdf.ln(10)

    # AI Insights
    pdf.set_font("Arial", style="B", size=14)
    pdf.cell(200, 10, txt="AI-Generated Insights", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, gemini_insights)

    pdf.ln(10)

    # Visualizations
    pdf.set_font("Arial", style="B", size=14)
    pdf.cell(200, 10, txt="Visualizations", ln=True)
    pdf.set_font("Arial", size=12)
    for viz_title, viz_path in visualizations.items():
        pdf.cell(200, 10, txt=viz_title, ln=True)
        pdf.image(viz_path, w=170)
        pdf.ln(10)

    return pdf

include_ai_insights = st.checkbox("Include AI Insights in the Report", value=False)
# Button to generate and download the report
if st.button("Download PDF Report"):
    with st.spinner("Generating PDF report..."):
        try:
            # Prepare KPIs, insights, and visualizations for the report
            kpis = {
                "Total Sales": f"${total_revenue:,}",
                "Total Profit": f"${total_profit:,}",
                "Total Orders": total_orders,
                "Average Sales/Order": f"${average_sales_per_order:,}",
                "Total Quantity Sold": total_quantity_sold,
                "Average Profit Margin": f"{average_profit_margin}%",
                "Sales per Customer": f"${sales_per_customer:,}",
                "Average Revenue per Transaction": f"${average_revenue_per_transaction:,}"
            }

            # Example paths to images for visualizations
            sales_profit_by_category_path = "sales_profit_by_category.png"
            sales_by_region_path = "sales_by_region.png"
            top_products_path = "top_products_by_revenue.png"
            revenue_trend_path = "revenue_trend.png"

            # Save visualizations to files
            fig_sales_profit_bar.write_image(sales_profit_by_category_path)
            fig_region.write_image(sales_by_region_path)
            fig_top_products.write_image(top_products_path)
            fig_trend.write_image(revenue_trend_path)

            visualizations = {
                "Sales and Profit by Product Category": sales_profit_by_category_path,
                "Revenue and Profit by Region": sales_by_region_path,
                "Top 5 Products by Total Revenue": top_products_path,
                "Revenue Trend Over Time": revenue_trend_path
            }

            # Conditionally include AI insights
            gemini_insights = st.session_state.get("gemini_insights", "No Gemini insights available.") if include_ai_insights else ""

            # Generate PDF
            pdf = generate_pdf_report(kpis, visualizations, gemini_insights)

            # Save PDF to a temporary file
            pdf_path = "AI_Sales_Dashboard_Report.pdf"
            pdf.output(pdf_path)

            # Encode PDF for download
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()

            b64 = base64.b64encode(pdf_data).decode()  # Base64 encoding
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="AI_Sales_Dashboard_Report.pdf">Click here to download the report</a>'
            st.markdown(href, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error generating PDF report: {e}")
