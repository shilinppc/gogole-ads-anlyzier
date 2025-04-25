import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import time
from helpers import validate_url, validate_budget
from calculator import generate_detailed_analysis
from database import save_analysis

# Page configuration
st.set_page_config(
    page_title="Google Ads Budget Analysis Tool (UAH)",
    page_icon="📊",
    layout="wide"
)

# App title
st.title("Google Ads Budget Analysis Tool")
st.markdown("Estimate costs, ROI, and ROAS for your Google Ad campaigns in Ukrainian Hryvnia (UAH)")

# Navigation links
col1, col2 = st.columns([3, 1])
with col2:
    st.markdown("[View Saved Analyses](/saved_analyses)", help="View previously saved analyses")

# Sidebar with inputs
with st.sidebar:
    st.header("Campaign Parameters")
    
    # Budget input with validation
    budget_input = st.text_input(
        "Google Ads Budget (UAH)",
        placeholder="Enter amount in UAH"
    )
    
    # Website URL input
    website_url = st.text_input(
        "Website URL",
        placeholder="e.g., example.com"
    )
    
    # Business type selection
    business_type = st.selectbox(
        "Business Type",
        options=["ecommerce", "services"],
        format_func=lambda x: "E-commerce" if x == "ecommerce" else "Services"
    )
    
    # Advanced parameters (collapsible)
    with st.expander("Advanced Parameters"):
        st.info("Adjust these parameters to fine-tune your estimates")
        
        if business_type == "ecommerce":
            avg_cpc = st.slider("Average Cost Per Click (UAH)", 5.0, 15.0, 10.0, 0.5)
            ctr = st.slider("Click-Through Rate (%)", 2.0, 4.0, 3.0, 0.1) / 100
            conversion_rate = st.slider("Conversion Rate (%)", 1.0, 3.0, 2.0, 0.1) / 100
            avg_order_value = st.slider("Average Order Value (UAH)", 800, 2000, 1400, 50)
        else:  # services
            avg_cpc = st.slider("Average Cost Per Click (UAH)", 8.0, 20.0, 14.0, 0.5)
            ctr = st.slider("Click-Through Rate (%)", 1.5, 3.5, 2.5, 0.1) / 100
            conversion_rate = st.slider("Conversion Rate (%)", 3.0, 7.0, 5.0, 0.1) / 100
            avg_order_value = st.slider("Average Order Value (UAH)", 1500, 5000, 3250, 50)
        
        advanced_params = {
            'avg_cpc': avg_cpc,
            'ctr': ctr,
            'conversion_rate': conversion_rate,
            'avg_order_value': avg_order_value
        }
    
    # Calculate button
    calculate_button = st.button("Calculate", type="primary", use_container_width=True)
    
    # Help information
    st.markdown("---")
    with st.expander("How it works"):
        st.markdown("""
        This tool helps you estimate the performance of your Google Ads campaigns based on your budget and business type.
        
        **Key Metrics:**
        - **ROI (Return on Investment)**: Measures the profitability of your ad spend relative to its cost.
        - **ROAS (Return on Ad Spend)**: The revenue generated for each UAH spent on ads.
        - **CPC (Cost Per Click)**: Average amount you pay for each click on your ad.
        - **CTR (Click-Through Rate)**: Percentage of ad impressions that result in clicks.
        - **Conversion Rate**: Percentage of clicks that result in a desired action.
        """)

# Main content area
# Input validation and calculations
if calculate_button:
    valid_budget, budget_value = validate_budget(budget_input)
    valid_url = validate_url(website_url)
    
    # Error messages for invalid inputs
    if not valid_budget:
        st.error("Please enter a valid budget amount in UAH.")
    if not valid_url:
        st.error("Please enter a valid website URL.")
    
    # If inputs are valid, proceed with calculations
    if valid_budget and valid_url:
        st.success(f"Analyzing campaign for {website_url} with a budget of {budget_value:,.2f} UAH")
        
        # Generate detailed analysis
        base_case, pessimistic_case, optimistic_case = generate_detailed_analysis(
            budget_value, 
            business_type,
            advanced_params
        )
        
        # Display results in 3 columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Expected Results")
            st.metric("Monthly Clicks", f"{int(base_case['clicks']):,}")
            st.metric("Monthly Conversions", f"{int(base_case['conversions']):,}")
            st.metric("Cost Per Conversion", f"{base_case['cost_per_conversion']:,.2f} UAH")
            st.metric("Monthly Revenue", f"{base_case['revenue']:,.2f} UAH")
            
        with col2:
            st.subheader("Return Metrics")
            st.metric("ROI", f"{base_case['roi']*100:.2f}%", help="Return on Investment")
            st.metric("ROAS", f"{base_case['roas']:.2f}x", help="Return on Ad Spend")
            st.metric("Profit", f"{base_case['revenue'] - budget_value:,.2f} UAH")
            st.metric("Breakeven CPC", f"{base_case['avg_order_value'] * base_case['conversion_rate']:,.2f} UAH")
            
        with col3:
            st.subheader("Campaign Overview")
            st.metric("Average CPC", f"{base_case['avg_cpc']:,.2f} UAH")
            st.metric("CTR", f"{base_case['ctr']*100:.2f}%")
            st.metric("Conversion Rate", f"{base_case['conversion_rate']*100:.2f}%")
            st.metric("Average Order Value", f"{base_case['avg_order_value']:,.2f} UAH")
        
        # Scenario comparison
        st.markdown("---")
        st.subheader("Scenario Analysis")
        
        # Create DataFrame for scenarios with numeric values (not formatted strings)
        scenarios_df = pd.DataFrame({
            'Metric': [
                'Clicks', 'Conversions', 'Revenue (UAH)', 
                'Cost Per Conversion (UAH)', 'ROI (%)', 'ROAS'
            ],
            'Pessimistic': [
                int(pessimistic_case['clicks']),
                int(pessimistic_case['conversions']),
                pessimistic_case['revenue'],
                pessimistic_case['cost_per_conversion'],
                pessimistic_case['roi']*100,
                pessimistic_case['roas']
            ],
            'Expected': [
                int(base_case['clicks']),
                int(base_case['conversions']),
                base_case['revenue'],
                base_case['cost_per_conversion'],
                base_case['roi']*100,
                base_case['roas']
            ],
            'Optimistic': [
                int(optimistic_case['clicks']),
                int(optimistic_case['conversions']),
                optimistic_case['revenue'],
                optimistic_case['cost_per_conversion'],
                optimistic_case['roi']*100,
                optimistic_case['roas']
            ]
        })
        
        # Format the table for display
        st.table(scenarios_df.style.format({
            'Pessimistic': lambda x: f"{x:,.2f}" if isinstance(x, float) else f"{x:,}",
            'Expected': lambda x: f"{x:,.2f}" if isinstance(x, float) else f"{x:,}",
            'Optimistic': lambda x: f"{x:,.2f}" if isinstance(x, float) else f"{x:,}"
        }))
        
        # Visualizations
        st.markdown("---")
        st.subheader("Performance Visualizations")
        
        # ROI comparison chart
        fig_roi = go.Figure()
        fig_roi.add_trace(go.Bar(
            x=['Pessimistic', 'Expected', 'Optimistic'],
            y=[
                pessimistic_case['roi']*100,
                base_case['roi']*100,
                optimistic_case['roi']*100
            ],
            text=[f"{pessimistic_case['roi']*100:.2f}%", 
                  f"{base_case['roi']*100:.2f}%", 
                  f"{optimistic_case['roi']*100:.2f}%"],
            textposition='auto',
            marker_color=['#FF9999', '#66B2FF', '#99CC99']
        ))
        fig_roi.update_layout(
            title='ROI Comparison by Scenario',
            xaxis_title='Scenario',
            yaxis_title='ROI (%)',
            height=400
        )
        
        # Revenue vs. Cost chart
        metrics_chart_data = pd.DataFrame({
            'Scenario': ['Pessimistic', 'Expected', 'Optimistic'],
            'Revenue': [
                pessimistic_case['revenue'],
                base_case['revenue'],
                optimistic_case['revenue']
            ],
            'Cost': [budget_value, budget_value, budget_value],
            'Profit': [
                pessimistic_case['revenue'] - budget_value,
                base_case['revenue'] - budget_value,
                optimistic_case['revenue'] - budget_value
            ]
        })
        
        fig_metrics = px.bar(
            metrics_chart_data,
            x='Scenario',
            y=['Revenue', 'Cost', 'Profit'],
            barmode='group',
            height=400,
            title='Revenue vs. Cost by Scenario',
            color_discrete_sequence=['#5D9CEC', '#ED5565', '#A0D468']
        )
        
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.plotly_chart(fig_roi, use_container_width=True)
        with col_chart2:
            st.plotly_chart(fig_metrics, use_container_width=True)
        
        # Key performance indicators chart
        kpi_data = pd.DataFrame({
            'KPI': ['Clicks', 'Conversions', 'Cost Per Conversion'],
            'Pessimistic': [
                pessimistic_case['clicks'],
                pessimistic_case['conversions'],
                pessimistic_case['cost_per_conversion']
            ],
            'Expected': [
                base_case['clicks'],
                base_case['conversions'],
                base_case['cost_per_conversion']
            ],
            'Optimistic': [
                optimistic_case['clicks'],
                optimistic_case['conversions'],
                optimistic_case['cost_per_conversion']
            ]
        })
        
        # Prepare data for radar chart
        categories = ['Clicks', 'Conversions', 'CPC', 'CTR', 'Conv. Rate', 'ROAS']
        
        # Normalize values for radar chart (0-1 scale)
        pessimistic_values = [
            pessimistic_case['clicks'] / optimistic_case['clicks'],
            pessimistic_case['conversions'] / optimistic_case['conversions'],
            optimistic_case['avg_cpc'] / pessimistic_case['avg_cpc'],  # Inverted for CPC (lower is better)
            pessimistic_case['ctr'] / optimistic_case['ctr'],
            pessimistic_case['conversion_rate'] / optimistic_case['conversion_rate'],
            pessimistic_case['roas'] / optimistic_case['roas']
        ]
        
        expected_values = [
            base_case['clicks'] / optimistic_case['clicks'],
            base_case['conversions'] / optimistic_case['conversions'],
            optimistic_case['avg_cpc'] / base_case['avg_cpc'],  # Inverted for CPC
            base_case['ctr'] / optimistic_case['ctr'],
            base_case['conversion_rate'] / optimistic_case['conversion_rate'],
            base_case['roas'] / optimistic_case['roas']
        ]
        
        optimistic_values = [1, 1, 1, 1, 1, 1]  # Optimistic is reference (all 1.0)
        
        fig_radar = go.Figure()
        
        fig_radar.add_trace(go.Scatterpolar(
            r=pessimistic_values,
            theta=categories,
            fill='toself',
            name='Pessimistic',
            line_color='#ED5565'
        ))
        
        fig_radar.add_trace(go.Scatterpolar(
            r=expected_values,
            theta=categories,
            fill='toself',
            name='Expected',
            line_color='#5D9CEC'
        ))
        
        fig_radar.add_trace(go.Scatterpolar(
            r=optimistic_values,
            theta=categories,
            fill='toself',
            name='Optimistic',
            line_color='#A0D468'
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            title='Campaign Performance Comparison',
            height=500
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)
        
        # Recommendations based on business type
        st.markdown("---")
        st.subheader("Recommendations")
        
        if business_type == "ecommerce":
            st.info("""
            ### E-commerce Recommendations:
            
            1. **Product-focused keywords**: Target specific product keywords for higher intent traffic.
            
            2. **Shopping campaigns**: Consider using Google Shopping campaigns to showcase products visually.
            
            3. **Remarketing**: Implement remarketing for cart abandoners to improve conversion rates.
            
            4. **Conversion optimization**: Focus on streamlining the checkout process to reduce abandonment.
            
            5. **Seasonal budgeting**: Increase budget during peak shopping seasons for maximum impact.
            """)
        else:  # services
            st.info("""
            ### Services Recommendations:
            
            1. **Local targeting**: Use location-based targeting for service area businesses.
            
            2. **Lead generation**: Focus on lead form extensions and call-only campaigns.
            
            3. **Long-tail keywords**: Target specific service-related long-tail keywords.
            
            4. **Customer testimonials**: Highlight reviews and testimonials in ad extensions.
            
            5. **Call tracking**: Implement call tracking to measure phone conversions accurately.
            """)
            
        # Export options
        st.markdown("---")
        st.subheader("Export Analysis")
        
        export_col1, export_col2 = st.columns(2)
        
        with export_col1:
            if st.button("📊 Export to Excel", use_container_width=True):
                try:
                    from export import export_to_excel
                    
                    # Prepare data for export
                    export_data = {
                        'website_url': website_url,
                        'budget': budget_value,
                        'business_type': business_type,
                        'base_case': base_case,
                        'pessimistic_case': pessimistic_case,
                        'optimistic_case': optimistic_case
                    }
                    
                    # Generate Excel file
                    excel_data = export_to_excel(export_data)
                    
                    # Create download button
                    st.download_button(
                        label="Download Excel File",
                        data=excel_data,
                        file_name=f"google_ads_analysis_{website_url.replace('.', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                except Exception as e:
                    st.error(f"Error exporting to Excel: {str(e)}")
        
        with export_col2:
            if st.button("📄 Export to PDF", use_container_width=True):
                try:
                    from export import export_to_pdf
                    
                    # Prepare data for export
                    export_data = {
                        'website_url': website_url,
                        'budget': budget_value,
                        'business_type': business_type,
                        'base_case': base_case,
                        'pessimistic_case': pessimistic_case,
                        'optimistic_case': optimistic_case
                    }
                    
                    # Generate PDF file
                    pdf_data = export_to_pdf(export_data)
                    
                    # Create download button
                    st.download_button(
                        label="Download PDF Report",
                        data=pdf_data,
                        file_name=f"google_ads_analysis_{website_url.replace('.', '_')}.pdf",
                        mime="application/pdf"
                    )
                    
                except Exception as e:
                    st.error(f"Error exporting to PDF: {str(e)}")
            
        # Save analysis to database option
        st.markdown("---")
        st.subheader("Save This Analysis")
        
        notes = st.text_area("Notes (optional)", placeholder="Add any notes about this analysis...")
        save_checkbox = st.checkbox("Mark as favorite", value=False)
        
        if st.button("Save Analysis", type="primary", use_container_width=True):
            try:
                # Prepare data for saving
                analysis_data = {
                    'website_url': website_url,
                    'budget': budget_value,
                    'business_type': business_type,
                    'advanced_params': advanced_params,
                    'base_case': base_case,
                    'pessimistic_case': pessimistic_case,
                    'optimistic_case': optimistic_case,
                    'notes': notes,
                    'is_saved': save_checkbox
                }
                
                # Save to database with retry logic
                retry_attempts = 3
                for attempt in range(retry_attempts):
                    try:
                        analysis_id = save_analysis(analysis_data)
                        
                        if analysis_id:
                            st.success(f"Analysis saved successfully! ID: {analysis_id}")
                            st.markdown("[View All Saved Analyses](/saved_analyses)")
                            break
                        else:
                            st.error("Error saving analysis. Please try again.")
                            break
                            
                    except Exception as e:
                        if attempt < retry_attempts - 1:
                            st.warning(f"Database connection issue. Retrying ({attempt+1}/{retry_attempts})...")
                            time.sleep(1)
                        else:
                            st.error(f"Database error after {retry_attempts} attempts: {str(e)}")
                            st.info("Please try again later or check the database connection.")
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")
            
        # Additional information and footnotes
        st.markdown("---")
        st.caption("""
        **Note**: These projections are estimates based on industry averages and the parameters you've provided. 
        Actual campaign performance may vary based on numerous factors including ad quality, targeting, market conditions, and competition.
        
        For best results, continuously monitor and optimize your campaigns based on real performance data.
        """)
else:
    # Default content when the app first loads
    st.info("""
    ### Welcome to the Google Ads Budget Analysis Tool!
    
    To get started:
    
    1. Enter your Google Ads budget in UAH
    2. Input your website URL
    3. Select your business type
    4. Adjust any advanced parameters (optional)
    5. Click "Calculate" to see your campaign projections
    
    The tool will provide you with estimated metrics including clicks, conversions, ROI, and ROAS
    based on typical performance indicators for your business type.
    """)
    
    st.markdown("""
    ### Why use this tool?
    
    - 📊 Get instant ROI and ROAS projections
    - 💰 Understand your cost per acquisition
    - 📈 Compare different budget scenarios
    - 🎯 Receive business-specific recommendations
    
    Ready to start planning your Google Ads campaign? Enter your information in the sidebar!
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center;'>"
    "Google Ads Budget Analysis Tool | "
    "Ukrainian Hryvnia (UAH) Calculator"
    "</div>", 
    unsafe_allow_html=True
)
