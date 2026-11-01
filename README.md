# 🛍️ Brazilian E-Commerce Analytics | Olist

### 📊 Transforming E-Commerce Data into Actionable Business Insights

An end-to-end **Business Analytics and Predictive Modelling Project** focused on analysing Brazilian e-commerce operations using Python, SQL Server, Power BI, and Streamlit.

This project explores sales performance, customer satisfaction, product and category trends, delivery efficiency, and seller performance. It combines business intelligence with predictive analytics to uncover meaningful patterns, identify operational risks, and support data-driven decision-making.

✨ From raw data to meaningful insights — this project demonstrates the complete analytics lifecycle, from data preparation and SQL-based analysis to interactive dashboards and machine learning.

---

## 💎 Project Highlights

- 📈 **Sales Analytics:** Revenue trends, order performance, and business growth.
- 🛒 **Product Analytics:** Category performance, product sales, and freight analysis.
- ❤️ **Customer Analytics:** Customer satisfaction, review patterns, and repeat purchasing.
- 🚚 **Delivery Analytics:** Delivery performance, delays, and logistics efficiency.
- 🏪 **Seller Analytics:** Seller revenue, ratings, and operational performance.
- ⚠️ **Risk Analytics:** Identification and monitoring of Key Risk Indicators (KRIs).
- 🤖 **Predictive Analytics:** Machine learning to analyse customer dissatisfaction.
- 🖥️ **Interactive Application:** Streamlit-based interface integrating business insights and predictive capabilities.

---

## 🎯 1. Project Objectives

The primary objective is to analyse the Brazilian e-commerce business ecosystem and transform transactional data into meaningful business insights.

The project aims to:

- Analyse overall sales and revenue performance.
- Identify high-performing products and categories.
- Evaluate customer satisfaction and review behaviour.
- Investigate delivery delays and logistics performance.
- Assess seller performance and operational efficiency.
- Identify potential business risks using Key Risk Indicators.
- Apply predictive modelling to understand customer dissatisfaction.
- Develop interactive dashboards for business reporting.
- Support informed and data-driven business decisions.

---

## 📂 2. Dataset Overview

The project uses the **Brazilian E-Commerce Public Dataset by Olist**.

The dataset contains information about e-commerce transactions, customers, sellers, products, payments, reviews, order items, and geographical locations.

### 🗃️ Cleaned SQL Server Tables

The project uses eight cleaned tables:

| Table | Description |
|---|---|
| `clean.order_360` | Order-level information and delivery details |
| `clean.customer_360` | Customer information |
| `clean.seller_360` | Seller information |
| `clean.items` | Order item and transaction details |
| `clean.products` | Product attributes and categories |
| `clean.reviews` | Customer review information |
| `clean.payments` | Payment transaction details |
| `clean.geolocation` | Geographical information |

These tables form the foundation of the analytical workflows and dashboard calculations.

---

## 🧰 3. Technology Stack

| Technology | Application |
|---|---|
| 🐍 Python | Data analysis, preprocessing and modelling |
| 🐼 Pandas | Data manipulation and analysis |
| 🔢 NumPy | Numerical operations |
| 📊 Matplotlib | Data visualization |
| 📈 Plotly | Interactive charts |
| 🗄️ SQL Server | Data storage and querying |
| 📉 Power BI | Business intelligence and dashboard development |
| 🖥️ Streamlit | Interactive web application |
| 🤖 Scikit-learn | Predictive modelling and evaluation |
| 🐙 Git & GitHub | Version control and project management |

---

## 🔄 4. Project Workflow

The project follows an end-to-end analytics workflow:

1. **Data Understanding:** Understanding the dataset, structure, business context and variables.
2. **Data Auditing:** Examining data quality, missing values, duplicates and inconsistencies.
3. **Data Cleaning:** Processing and preparing the raw datasets.
4. **SQL Data Preparation:** Creating and maintaining eight cleaned analytical tables.
5. **Exploratory Data Analysis:** Identifying patterns, trends and relationships.
6. **Descriptive Analytics:** Measuring business performance using KPIs.
7. **Diagnostic Analytics:** Investigating the factors influencing business outcomes.
8. **Risk Analytics:** Defining and analysing Key Risk Indicators.
9. **Dashboard Development:** Building interactive Power BI dashboards.
10. **Predictive Modelling:** Applying machine learning to analyse customer dissatisfaction.
11. **Streamlit Development:** Integrating the analytical components into an interactive application.

---

## 📊 5. Power BI Dashboard Overview

The Power BI dashboard is organised into five analytical sections.

### 📈 5.1 Executive Sales Overview

Focus: Understanding overall business and revenue performance.

**Key Performance Indicators:**
- Total Revenue
- Orders
- Average Order Value (AOV)
- Revenue Month-over-Month %

**Visualisations:**
- Monthly Revenue and Orders Trend
- Payment Methods
- Revenue by State — Top 10

**Business Purpose:** Understand revenue generation, order trends, payment preferences and geographical sales distribution.

### 🛒 5.2 Product and Category

Focus: Evaluating product and category performance.

**Key Performance Indicators:**
- Items Sold
- Top Category Share %
- Category Sales
- Top 10 Categories Share %

**Visualisations:**
- Top 10 Categories by Sales
- Low-Review % by Category
- Freight Cost % by Category

**Business Purpose:** Identify high-performing categories, understand category-level customer feedback and evaluate freight cost distribution.

### ❤️ 5.3 Customer and Satisfaction

Focus: Understanding customer experience and purchasing behaviour.

**Key Performance Indicators:**
- Average Review Score
- Satisfied Orders (4–5 Stars)
- Low Reviews (1–2 Stars)
- Repeat Customers

**Visualisations:**
- Average Review Score by Month
- Average Score by Delivery Delay
- Star Rating Split

**Business Purpose:** Evaluate customer satisfaction, review behaviour and repeat purchasing patterns.

### 🚚 5.4 Delivery and Logistics

Focus: Evaluating order fulfilment and delivery efficiency.

**Key Performance Indicators:**
- On-Time Delivery Rate
- Late Orders
- Average Days Late (Late Orders)
- Average Delivery Time (Days)

**Visualisations:**
- Late % by State — Top 10
- Estimated vs Actual Delivery Days
- Late % by Month
- Late vs On-Time among 1–2 Star Orders

**Business Purpose:** Identify delivery inefficiencies, investigate late deliveries and understand the relationship between delivery performance and customer feedback.

### 🏪 5.5 Seller Performance

Focus: Analysing seller contribution and operational performance.

**Key Performance Indicators:**
- Total Seller Revenue
- Active Sellers
- Average Seller Rating
- Seller Late Rate

**Visualisations:**
- Top 10 Sellers by Revenue
- Top 10 Sellers by Late Delivery Rate
- Sellers by Performance Group

**Business Purpose:** Evaluate seller contribution, operational efficiency and delivery-related performance.

---

## ⚠️ 6. Key Performance Indicators and Risk Indicators

The project incorporates both KPIs and KRIs to evaluate business performance.

### 📌 Key Performance Indicators (KPIs)

KPIs are used to measure business performance across:

- Revenue generation
- Order performance
- Average order value
- Customer satisfaction
- Repeat purchasing
- Delivery efficiency
- Seller performance
- Product and category contribution

### 🚨 Key Risk Indicators (KRIs)

KRIs are used to monitor potential operational and customer-related risks.

The analysis considers areas such as:

- Low customer review percentages
- Late delivery rates
- Product category-related risks
- Seller delivery performance
- Payment-related inconsistencies
- Order cancellation and unavailability patterns

The purpose is to identify potential problem areas and support proactive business monitoring.

---

## 🤖 7. Predictive Analytics and Machine Learning

The project incorporates predictive modelling to analyse customer dissatisfaction.

### 🎯 Prediction Objective

The modelling task focuses on identifying orders associated with low customer review scores.

The target variable is based on customer satisfaction:

- **Satisfied:** Review score of 4–5.
- **Not Satisfied:** Review score below 4.

### ⚙️ Modelling Workflow

1. Feature preparation and screening.
2. Data cleaning and preprocessing.
3. Feature selection and multicollinearity checks.
4. Train-test splitting.
5. Logistic Regression modelling.
6. Model evaluation.
7. Feature interpretation.

### 📊 Model Evaluation Metrics

The model is evaluated using:

| Metric | Purpose |
|---|---|
| Accuracy | Overall classification correctness |
| Precision | Correctness of positive predictions |
| Recall | Ability to identify positive cases |
| F1-score | Balance between precision and recall |
| ROC-AUC | Ability to distinguish between classes |

The modelling approach aims to understand the factors associated with customer dissatisfaction and provide analytical support for proactive business decisions.

*Actual model performance is reported through the trained model's evaluation results.*

---

## 🖥️ 8. Streamlit Application

The project includes a Streamlit application that brings together business intelligence and predictive analytics through an interactive interface.

### Application Sections

| Section | Purpose |
|---|---|
| 🏠 Home | Application landing page |
| 📊 Insights | Interactive business analytics dashboard |
| 🔮 Predict | Customer dissatisfaction prediction |
| 🤖 Model | Model performance and evaluation |

The application is designed to make business insights and predictive outputs accessible through a single interface.

---

## 📁 9. Project Structure

```text
olist-ecommerce-analytics/
│
├── app.py
│
├── pages/
│   ├── 1_Insights.py
│   ├── 2_Predict.py
│   └── 3_Model.py
│
├── src/
│   ├── data_loader.py
│   ├── analysis.py
│   ├── charts.py
│   ├── auth.py
│   ├── train_model.py
│   └── build_app_data.py
│
├── outputs/
│   └── app_data/
│
├── requirements.txt
├── .gitignore
└── README.md
```

*This represents the main application structure. Additional scripts, assets, model files and configuration files may be included in the repository.*

---

## ⚙️ 10. Installation and Setup

Follow these steps to run the application locally.

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/olist-ecommerce-analytics.git
```

Replace `YOUR-USERNAME` with your GitHub username.

### Step 2: Navigate to the Project Directory

```bash
cd olist-ecommerce-analytics
```

### Step 3: Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the environment on Windows:

```powershell
.venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Configure SQL Server

The current application uses SQL Server with Windows Authentication.

**Database Name:**

```text
PRP_OLIST_PROJECT
```

**Schema:**

```text
clean
```

Ensure that the eight cleaned tables are available in the configured SQL Server database.

Also ensure that the required SQL Server ODBC driver is installed.

### Step 6: Generate Application Data

```bash
python -m src.build_app_data
```

### Step 7: Train the Predictive Model

```bash
python -m src.train_model
```

Run this command if the required trained model artifacts have not already been generated.

### Step 8: Launch the Application

```bash
streamlit run app.py
```

The application will open in your default browser.

---

## ☁️ 11. Deployment

The Streamlit application can be deployed using Streamlit Community Cloud.

### Deployment Steps

1. Push the project to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/).
3. Connect your GitHub account.
4. Select the project repository.
5. Select `app.py` as the main application file.
6. Configure the required dependencies and application secrets.
7. Deploy the application.

### ⚠️ Important Deployment Consideration

The current project uses a locally hosted SQL Server database.

A cloud-hosted Streamlit application cannot directly access a SQL Server instance running only on a personal computer.

For successful cloud deployment, the database must be made accessible through a suitable secure cloud-hosted database or another appropriate data-hosting solution.

Never upload database passwords, API keys, authentication secrets or sensitive customer information to a public GitHub repository.

---

## 💼 12. Business Value

This project demonstrates how business analytics and predictive modelling can be integrated to support e-commerce decision-making.

The analytical framework helps explore:

- 📈 Revenue generation and sales trends.
- 🛒 Product and category performance.
- ❤️ Customer satisfaction and purchasing behaviour.
- 🚚 Delivery and logistics efficiency.
- 🏪 Seller contribution and performance.
- ⚠️ Potential operational risks.
- 🤖 Customer dissatisfaction prediction.

By combining descriptive, diagnostic and predictive analytics, the project demonstrates how data can be transformed into meaningful business intelligence.

---

## 🌱 13. Skills Demonstrated

- Data Understanding and Data Auditing
- Data Cleaning and Preprocessing
- SQL Querying and Database Management
- Exploratory Data Analysis
- Descriptive and Diagnostic Analytics
- KPI and KRI Development
- Data Visualization
- Power BI Dashboard Development
- Python Programming
- Machine Learning
- Predictive Analytics
- Streamlit Application Development
- Git and GitHub

---

## 🔮 14. Future Scope

Potential enhancements include:

- Integration with a cloud-hosted database.
- Automated data refresh and reporting.
- Further predictive modelling approaches.
- Improved model interpretability.
- Additional business risk monitoring.
- Enhanced interactive dashboard capabilities.

---

## 👩‍💻 15. Project Information

**Project:** Brazilian E-Commerce Analytics — Olist

**Domain:** Business Analytics | E-Commerce | Predictive Analytics

**Primary Tools:** Python, SQL Server, Power BI, Streamlit and Scikit-learn

**Dataset:** Brazilian E-Commerce Public Dataset by Olist

**Project Type:** End-to-End Business Analytics Project

---

## ✨ Final Note

This project represents the integration of data analytics, business intelligence and predictive modelling to understand real-world e-commerce operations.

**Turning data into insights. Turning insights into decisions.** 🚀

---

<p align="center">
  <b>💜 Built with Python, SQL, Power BI & Streamlit</b>
  <br>
  <i>Data-driven thinking. Business-focused insights. Continuous learning.</i>
</p>
