import streamlit as st
import pandas as pd
import datetime
import json
import time
import ast  # For safely parsing string representations of dictionaries
from database import get_all_analyses, get_analysis_by_id, delete_analysis, update_analysis_notes

# Page configuration
st.set_page_config(
    page_title="Saved Analyses - Google Ads Budget Tool (UAH)",
    page_icon="📊",
    layout="wide"
)

# Page header
st.title("Saved Analysis Reports")
st.markdown("View and manage your previously saved Google Ads budget analyses")

# Get all analyses from database
retry_count = 0
max_retries = 3
analyses = None

while retry_count < max_retries:
    try:
        analyses = get_all_analyses(limit=50)
        break  # If successful, exit the retry loop
    except Exception as e:
        retry_count += 1
        if retry_count < max_retries:
            st.warning(f"Database connection issue. Retrying... ({retry_count}/{max_retries})")
            time.sleep(1)  # Short delay before retrying
        else:
            st.error(f"Error retrieving analyses after {max_retries} attempts: {str(e)}")
            st.info("Please try refreshing the page or check database connection settings.")
            analyses = None

if analyses is None:
    st.info("No analyses available. Go to the main page to create a new analysis.")
elif not analyses:
    st.info("No saved analyses found. Go to the main page to create a new analysis.")
else:
    # Create a DataFrame for display
    analyses_data = []
    
    for analysis in analyses:
        # Format the date
        created_at = analysis.created_at.strftime("%Y-%m-%d %H:%M")
        
        # Format values for display
        analyses_data.append({
            "ID": analysis.id,
            "Date": created_at,
            "Website": analysis.website_url,
            "Budget (UAH)": f"{analysis.budget:,.2f}",
            "Business Type": "E-commerce" if analysis.business_type == "ecommerce" else "Services",
            "ROI": f"{analysis.roi*100:.2f}%",
            "ROAS": f"{analysis.roas:.2f}x",
            "Saved": "✓" if analysis.is_saved else "",
            "Notes": analysis.notes[:30] + "..." if analysis.notes and len(analysis.notes) > 30 else analysis.notes
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(analyses_data)
    
    # Display the table with sorting
    st.dataframe(
        df,
        column_config={
            "ID": st.column_config.NumberColumn("ID", help="Analysis ID", format="%d"),
            "Date": st.column_config.TextColumn("Date", help="Creation date"),
            "Website": st.column_config.TextColumn("Website", help="Website URL"),
            "Budget (UAH)": st.column_config.TextColumn("Budget (UAH)", help="Budget amount"),
            "Business Type": st.column_config.TextColumn("Business Type", help="Business type"),
            "ROI": st.column_config.TextColumn("ROI", help="Return on Investment"),
            "ROAS": st.column_config.TextColumn("ROAS", help="Return on Ad Spend"),
            "Saved": st.column_config.CheckboxColumn("Saved", help="Marked as favorite"),
            "Notes": st.column_config.TextColumn("Notes", help="User notes")
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Allow user to select analysis to view
    st.markdown("---")
    st.subheader("View Analysis Details")
    
    # Create a list of options for the selectbox
    analysis_options = [f"ID {analysis.id}: {analysis.website_url} - {analysis.budget:,.2f} UAH ({created_at})" 
                       for analysis, created_at in 
                       [(a, a.created_at.strftime("%Y-%m-%d")) for a in analyses]]
    
    selected_analysis_index = st.selectbox(
        "Select an analysis to view:",
        options=range(len(analysis_options)),
        format_func=lambda i: analysis_options[i]
    )
    
    if selected_analysis_index is not None:
        # Get the selected analysis
        selected_analysis = analyses[selected_analysis_index]
        
        # Display analysis details
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### Analysis for {selected_analysis.website_url}")
            st.markdown(f"**Created:** {selected_analysis.created_at.strftime('%Y-%m-%d %H:%M')}")
            st.markdown(f"**Budget:** {selected_analysis.budget:,.2f} UAH")
            st.markdown(f"**Business Type:** {'E-commerce' if selected_analysis.business_type == 'ecommerce' else 'Services'}")
            
            # Display notes with update capability
            notes = st.text_area(
                "Notes", 
                value=selected_analysis.notes if selected_analysis.notes else "",
                height=150
            )
            
            is_saved = st.checkbox(
                "Mark as favorite", 
                value=selected_analysis.is_saved
            )
            
            if st.button("Update Notes"):
                if update_analysis_notes(selected_analysis.id, notes, is_saved):
                    st.success("Notes updated successfully.")
                    st.rerun()
                else:
                    st.error("Failed to update notes.")
            
            if st.button("Delete Analysis", type="primary", use_container_width=True):
                if delete_analysis(selected_analysis.id):
                    st.success("Analysis deleted successfully.")
                    st.rerun()
                else:
                    st.error("Failed to delete analysis.")
        
        with col2:
            # Display key metrics
            st.markdown("### Key Metrics")
            
            metric_col1, metric_col2 = st.columns(2)
            
            with metric_col1:
                st.metric("ROI", f"{selected_analysis.roi*100:.2f}%")
                st.metric("ROAS", f"{selected_analysis.roas:.2f}x")
                st.metric("Revenue", f"{selected_analysis.revenue:,.2f} UAH")
            
            with metric_col2:
                st.metric("Clicks", f"{int(selected_analysis.clicks):,}")
                st.metric("Conversions", f"{int(selected_analysis.conversions):,}")
                st.metric("Cost Per Conversion", f"{selected_analysis.cost_per_conversion:,.2f} UAH")
            
            # Parameter settings
            st.markdown("### Parameter Settings")
            st.markdown(f"**Average CPC:** {selected_analysis.avg_cpc:,.2f} UAH")
            st.markdown(f"**CTR:** {selected_analysis.ctr*100:.2f}%")
            st.markdown(f"**Conversion Rate:** {selected_analysis.conversion_rate*100:.2f}%")
            st.markdown(f"**Average Order Value:** {selected_analysis.avg_order_value:,.2f} UAH")
            
            # Export options
            st.markdown("### Export Options")
            
            export_col1, export_col2 = st.columns(2)
            
            with export_col1:
                if st.button("📊 Export to Excel", key="excel_export", use_container_width=True):
                    try:
                        from export import export_to_excel
                        import json
                        
                        # Convert stored JSON strings back to dictionaries
                        try:
                            pessimistic_case = json.loads(selected_analysis.pessimistic_scenario)
                        except:
                            # Fallback if JSON parsing fails
                            pessimistic_case = {}
                            
                        try:
                            optimistic_case = json.loads(selected_analysis.optimistic_scenario)
                        except:
                            # Fallback if JSON parsing fails
                            optimistic_case = {}
                        
                        # Prepare base case data
                        base_case = {
                            'clicks': selected_analysis.clicks,
                            'impressions': selected_analysis.impressions,
                            'conversions': selected_analysis.conversions,
                            'cost_per_conversion': selected_analysis.cost_per_conversion,
                            'revenue': selected_analysis.revenue,
                            'roi': selected_analysis.roi,
                            'roas': selected_analysis.roas,
                            'avg_cpc': selected_analysis.avg_cpc,
                            'ctr': selected_analysis.ctr,
                            'conversion_rate': selected_analysis.conversion_rate,
                            'avg_order_value': selected_analysis.avg_order_value
                        }
                        
                        # Prepare data for export
                        export_data = {
                            'website_url': selected_analysis.website_url,
                            'budget': selected_analysis.budget,
                            'business_type': selected_analysis.business_type,
                            'base_case': base_case,
                            'pessimistic_case': pessimistic_case,
                            'optimistic_case': optimistic_case,
                            'notes': selected_analysis.notes
                        }
                        
                        # Generate Excel file
                        excel_data = export_to_excel(export_data)
                        
                        # Create download button
                        st.download_button(
                            label="Download Excel File",
                            data=excel_data,
                            file_name=f"google_ads_analysis_{selected_analysis.id}_{selected_analysis.website_url.replace('.', '_')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
                    except Exception as e:
                        st.error(f"Error exporting to Excel: {str(e)}")
            
            with export_col2:
                if st.button("📄 Export to PDF", key="pdf_export", use_container_width=True):
                    try:
                        from export import export_to_pdf
                        import json
                        
                        # Convert stored JSON strings back to dictionaries
                        try:
                            pessimistic_case = json.loads(selected_analysis.pessimistic_scenario)
                        except:
                            # Fallback if JSON parsing fails
                            pessimistic_case = {}
                            
                        try:
                            optimistic_case = json.loads(selected_analysis.optimistic_scenario)
                        except:
                            # Fallback if JSON parsing fails
                            optimistic_case = {}
                        
                        # Prepare base case data
                        base_case = {
                            'clicks': selected_analysis.clicks,
                            'impressions': selected_analysis.impressions,
                            'conversions': selected_analysis.conversions,
                            'cost_per_conversion': selected_analysis.cost_per_conversion,
                            'revenue': selected_analysis.revenue,
                            'roi': selected_analysis.roi,
                            'roas': selected_analysis.roas,
                            'avg_cpc': selected_analysis.avg_cpc,
                            'ctr': selected_analysis.ctr,
                            'conversion_rate': selected_analysis.conversion_rate,
                            'avg_order_value': selected_analysis.avg_order_value
                        }
                        
                        # Prepare data for export
                        export_data = {
                            'website_url': selected_analysis.website_url,
                            'budget': selected_analysis.budget,
                            'business_type': selected_analysis.business_type,
                            'base_case': base_case,
                            'pessimistic_case': pessimistic_case,
                            'optimistic_case': optimistic_case,
                            'notes': selected_analysis.notes
                        }
                        
                        # Generate PDF file
                        pdf_data = export_to_pdf(export_data)
                        
                        # Create download button
                        st.download_button(
                            label="Download PDF Report",
                            data=pdf_data,
                            file_name=f"google_ads_analysis_{selected_analysis.id}_{selected_analysis.website_url.replace('.', '_')}.pdf",
                            mime="application/pdf"
                        )
                        
                    except Exception as e:
                        st.error(f"Error exporting to PDF: {str(e)}")

# Link back to main page
st.markdown("---")
st.markdown("[⬅️ Back to Analysis Tool](./)")