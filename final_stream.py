import streamlit as st
from reportlab.pdfgen import canvas
from PyPDF2 import PdfWriter, PdfReader
from io import BytesIO
import base64
import pandas as pd
from PyPDF2 import PdfWriter, PdfReader
from pdf_mail import sendpdf
import os
import numpy as np

def create_text_pdf(text_list, filename, font_name="Helvetica", font_size=12, page_width=612, page_height=792):
    c = canvas.Canvas(filename, pagesize=(page_width, page_height))
    c.setFont(font_name, font_size)
    for text_item in text_list:
        c.setFont(text_item.get("font_name", font_name), text_item.get("font_size", font_size))
        c.drawString(text_item["x"], text_item["y"], text_item["text"])  # Draw text at specified coordinates
    c.save()

# Function to overlay multiple texts on a PDF
def add_text_to_pdf(original_pdf, text_list, output_pdf, page_number=0):
    reader1 = PdfReader(original_pdf)
    original_page = reader1.pages[page_number]
    page_width = float(original_page.mediabox.right)
    page_height = float(original_page.mediabox.top)
    temp_pdf = "temp.pdf"
    create_text_pdf(text_list, temp_pdf, page_width=page_width, page_height=page_height)
    reader2 = PdfReader(temp_pdf)
    writer = PdfWriter()
    for i, page in enumerate(reader1.pages):
        if i == page_number:
            page.merge_page(reader2.pages[0])
        writer.add_page(page)
    with open(output_pdf, "wb") as f_out:
        writer.write(f_out)
    os.remove(temp_pdf)
# Function to create a PDF with overlay text
def create_sample_pdf(name, x, y, font_name="Helvetica", font_size=12, page_width=612, page_height=792):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    c.setFont(font_name, font_size)
    c.drawString(x, y, name)  # Draw the name at specified coordinates
    c.save()
    buffer.seek(0)
    return buffer

# Function to overlay text on an existing PDF and return the modified PDF
def overlay_text_on_pdf(base_pdf, name, x, y, font_name, font_size):
    reader = PdfReader(base_pdf)
    page = reader.pages[0]
    page_width = float(page.mediabox.right)
    page_height = float(page.mediabox.top)

    # Create a temporary overlay PDF
    overlay_buffer = create_sample_pdf(name, x, y, font_name, font_size, page_width, page_height)

    # Merge the overlay with the original PDF
    overlay_reader = PdfReader(overlay_buffer)
    page.merge_page(overlay_reader.pages[0])

    writer = PdfWriter()
    output_buffer = BytesIO()
    writer.add_page(page)
    writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer

# Streamlit Sidebar Menu
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to:", ["Set Up Coordinates", "Certificate Generation and Sending","Help"])

if "saved_coordinates" not in st.session_state:
    st.session_state.saved_coordinates = {}

if menu == "Set Up Coordinates":
    # Set Up Coordinates Section
    st.title("Set Up Coordinates for Certificate")
    st.write("Upload a sample certificate and adjust the position of the participant's name or other attributes.")

    # Upload Sample Certificate
    sample_certificate = st.file_uploader("Upload a Sample Certificate (PDF)", type=["pdf"])
    participant_data = st.file_uploader("Upload Participant Data (Excel) to get suggestion of longest value of each column", type=["xlsx"])
    if participant_data:
        # Load participant data to get attribute names
        data = pd.read_excel(participant_data)
        column_names = data.columns.tolist()

        # Remove "Mail" attribute from column names
        if "Mail" in column_names:
            column_names.remove("Mail")
        #maarpu
        longest={}
        for x in column_names:
            a=np.array(data[x])
            try:
                if(type(a[0])==type("college")):
                    b=list(map(lambda y:len(y),a))
                    l=max(b)
                    longest[x]=a[b.index(l)]
            except:
                st.write("Excel Sheet has an issue of Data Missing i.e. every column of every row is not filled properly")
        st.write(longest)
    if sample_certificate:
        # Save uploaded certificate temporarily
        with open("sample_template.pdf", "wb") as f:
            f.write(sample_certificate.read())

        st.write("Adjust the position of the selected attribute using the sliders below.")

        # Attribute Input
        attribute_name = st.text_input("Enter the attribute you are setting up (e.g., Name):", "")
        value_name=st.text_input("Enter the value of that attribute(Better to try with longest value as suggested above):","")

        # Coordinate Inputs
        font_name = st.text_input("Font Name:", "Times-BoldItalic")
        st.write("Move the Sliders below to view the Preview")
        font_size = st.slider("Font Size:", 10, 50, 26)
        x_position = st.slider("X Coordinate:", 0, 600, 200)
        y_position = st.slider("Y Coordinate:", 0, 800, 400)
        

        # Generate Preview
        if attribute_name:
            modified_pdf = overlay_text_on_pdf(
                "sample_template.pdf",
                value_name,
                x_position,
                y_position,
                font_name,
                font_size,
            )

            st.write("### Preview of Certificate")
            pdf_data = modified_pdf.getvalue()
            pdf_base64 = base64.b64encode(pdf_data).decode("utf-8")
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="700" height="500"></iframe>',
                unsafe_allow_html=True,
            )

        # Save Coordinates Button
        if st.button("Save Coordinates"):
            if attribute_name:
                st.session_state.saved_coordinates[attribute_name] = {
                    "x": x_position,
                    "y": y_position,
                    "font_name": font_name,
                    "font_size": font_size,
                }
                st.success(f"Coordinates for '{attribute_name}' saved successfully!")
            else:
                st.error("Please enter an attribute name before saving.")

    # Display Saved Coordinates in Navigation Bar
    if st.session_state.saved_coordinates:
        st.sidebar.subheader("Saved Attribute Settings")
        for attribute, coords in st.session_state.saved_coordinates.items():
            st.sidebar.write(
                f"**{attribute}**: X={coords['x']}, Y={coords['y']}, Font={coords['font_name']}, Size={coords['font_size']}"
            )

elif menu == "Certificate Generation and Sending":
    if st.session_state.saved_coordinates:
        st.sidebar.subheader("Saved Attribute Settings")
        for attribute, coords in st.session_state.saved_coordinates.items():
            st.sidebar.write(
                f"**{attribute}**: X={coords['x']}, Y={coords['y']}, Font={coords['font_name']}, Size={coords['font_size']}"
            )
##    st.write("This section will allow you to upload participant data and generate/send certificates.")
##
##    # Display Saved Coordinates for Reference
##    if st.session_state.saved_coordinates:
##        st.write("### Saved Coordinates")
##        for attribute, coords in st.session_state.saved_coordinates.items():
##            st.write(
##                f"**{attribute}**: X={coords['x']}, Y={coords['y']}, Font={coords['font_name']}, Size={coords['font_size']}"
##            )
##    else:
##        st.write("No coordinates saved yet. Please set up coordinates in the 'Set Up Coordinates' tab.")
    st.title("Certificate Generator and Email Sender")
    st.write("Upload participant data, certificate template, and customize your email content.")

    # File Uploads
    st.write("⚠Note :Your Excel Data attributes should be in this format Name,Email,.... likewise")
    participant_data = st.file_uploader("Upload Participant Data (Excel)", type=["xlsx"])
    certificate_template = st.file_uploader("Upload Certificate Template (PDF)", type=["pdf"])

    # Email Credentials and Content
    sender_email = st.text_input("Sender Email")
    st.markdown("[Click here to know the setting of App Password to your G-Mail](https://youtu.be/MkLX85XU5rU?si=xhs78FRrWIPF0FGL)")
    sender_password = st.text_input("Sender Email App Security Key", type="password")
    email_subject = st.text_input("Email Subject", "Participation Certificate")
    email_body = st.text_area(
        "Email Body",
        '''Thank you for joining our event! Please find your certificate attached.''',
    )

    if participant_data:
        # Load participant data to get attribute names
        data = pd.read_excel(participant_data)
        column_names = data.columns.tolist()

        # Remove "Mail" attribute from column names
        if "Mail" in column_names:
            column_names.remove("Mail")
        #maarpu
        longest={}
        for x in column_names:
            a=np.array(data[x])
            try:
                if(type(a[0])==type("college")):
                    b=list(map(lambda y:len(y),a))
                    l=max(b)
                    longest[x]=l
            except:
                st.write("Excel Sheet has an issue of Data Missing i.e. every column of every row is not filled properly")

        # Display input fields for X and Y coordinates for each attribute (except "Mail")
        coordinates = {}
        for column in column_names:
            st.write(f"Enter X and Y coordinates for {column}")
            x_coord = st.number_input(f"X Coordinate for {column}", value=197)
            y_coord = st.number_input(f"Y Coordinate for {column}", value=334)
            font_name=st.number_input(f"Font Size for {column}",value=20)
            coordinates[column] = {"x": x_coord, "y": y_coord, "font":font_name}

    # Certificate Generation Settings
    font_name = st.text_input("Font Name", "Times-BoldItalic")
    #font_size = st.slider("Font Size", 10, 50, 26)

    # Output Directory
    output_directory = st.text_input("Enter the path where to save the genearted certificates in your System(Path Should be in the format (C:/users/Desktop)", "")

    if st.button("Generate Certificates and Send Emails"):
        if not participant_data or not certificate_template or not sender_email or not sender_password:
            st.error("Please provide all required inputs!")
        else:
            try:
                st.write("Generation and Sending Mails are Running...........")
                # Create output directory if it doesn't exist
                os.makedirs(output_directory, exist_ok=True)

                # Save certificate template locally
                with open("template.pdf", "wb") as f:
                    f.write(certificate_template.read())

                # Generate certificates and send emails for each participant
                for i, row in data.iterrows():
                    try:
                        name = row["Name"].title()
                        email = row["Mail"]
                        output_pdf = os.path.join(output_directory, f"{email[:-6]}.pdf.pdf")

                        # Prepare text list based on the coordinates entered by the user
                        text_list = []
                        for column in column_names:
                            if column in coordinates:
                                text = row[column]
                                text_list.append({
                                    #maarpu
                                    "text": (str(text).title()).center(longest[column]),
                                    "x": coordinates[column]["x"],
                                    "y": coordinates[column]["y"],
                                    "font_name": font_name,
                                    "font_size": coordinates[column]["font"]
                                })

                        # Add text to the certificate
                        add_text_to_pdf("template.pdf", text_list, output_pdf)

                        # Prepare email message
                        personalized_message = (
                            f"Hey {name.title()}!!!\n\n" + email_body
                        )

                        # Send email with the certificate
                        k = sendpdf(
                            sender_email, email, sender_password, email_subject,
                            personalized_message, f"{email[:-6]}.pdf", output_directory
                        )
                        k.email_send()

                    except Exception as e:
                        st.warning(f"Failed to send email to {email}")

                st.success("Certificates generated and emails sent successfully!")
            except Exception as e:
                st.error(f"An error occurred: {e}")
elif(menu=="Help"):
    st.write("You can Send Certificatificates to the Members who are in the Excel File.\nYou First Set Up the Coordinates for every attributes in Set Up Coordinates tab and save for data of each attribute.")
    st.write("Now Saved data is get displayed in the Navigation Menu.\nYou now visit the Certificates Generation and Sending tab and you can upload the excel file and Empty Certificate Template.")
    st.write("Now You enter your Mail ID and that mail's App Security Key to send mails from that Mail\n(If You don't know how to set up App Password then click the below Link to watch a Youtube Video!!!")
    st.markdown("[Click here to know the setting of App Password to your G-Mail](https://youtu.be/MkLX85XU5rU?si=xhs78FRrWIPF0FGL)")
    st.write("Now You can Set the coordinates and Font Sizes for each and every attribute by seeing the saved data in Navigation Menu.")
    st.write("Now You can set the Font Style and Now You can set the Path where all the generated certifictes are to be saved in your System\nNow You can click the Certificate Generate and Send Button.")
    st.write("Your Mails are now being generated and are being saved in the loaction you have given and are being sent to those Mails.")
    st.write("If any Email is not sent You will see that mail id below there itself.")
    st.write("If any error occurs then Error will get Displayed. You can try again by refreshing the site!!!")
