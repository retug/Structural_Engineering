import os
from PIL import Image, ImageDraw, ImageFont
import math

# Function to create a PDF from 4 images with filenames as titles

# Function to create a PDF from 4 images with filenames as titles
# Function to create a PDF from 4 images with filenames as titles
def create_pdf(images, filenames, pdf_path, pdf_page_width, pdf_page_height, dpi):
    # Create a canvas for an 8.5 x 11 inch page in pixels at the given DPI
    pdf_canvas = Image.new('RGB', (pdf_page_width, pdf_page_height), 'white')
    thumbnail_size = (int(pdf_page_width / 2), int(pdf_page_height / 2))

    # Positions for 2x2 grid
    positions = [(0, 0), (thumbnail_size[0], 0), (0, thumbnail_size[1]), (thumbnail_size[0], thumbnail_size[1])]

    # Create ImageDraw object for text drawing
    draw = ImageDraw.Draw(pdf_canvas)

    # Define font size (adjust according to needs)
    try:
        font = ImageFont.truetype("arial.ttf", 40)  # Use Arial or any preferred font, adjust size if needed
    except IOError:
        font = ImageFont.load_default()  # Fallback to default font if Arial not available

    for i, (img, filename) in enumerate(zip(images, filenames)):
        # Reserve 20% of the quadrant height for the text
        image_area_height = int(thumbnail_size[1] * 0.8)
        text_area_height = int(thumbnail_size[1] * 0.1)

        # Manually scale the image to 80% of the available area, preserving the aspect ratio
        aspect_ratio = img.width / img.height
        if img.width > img.height:
            # Horizontal image: fit width to 80% of the area
            new_width = int(thumbnail_size[0] * 0.8)
            new_height = int(new_width / aspect_ratio)
        else:
            # Vertical or square image: fit height to 80% of the area
            new_height = int(image_area_height)
            new_width = int(new_height * aspect_ratio)

        # Resize the image
        img = img.resize((new_width, new_height))

        # Create a drawing context for adding text
        draw_img = ImageDraw.Draw(pdf_canvas)

        # Get the filename without the extension and create the text to display
        text = filename  # Filename without the extension

        # Get the text bounding box (Pillow >= 8.0.0)
        bbox = draw_img.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        # Calculate the position to center the text in the top 20% of the quadrant
        text_position_x = (thumbnail_size[0] - text_width) // 2
        text_position_y = positions[i][1] + (text_area_height - 40) // 2  # Adjust y-position to vertically center text

        # Draw the text on the PDF canvas
        draw.text((positions[i][0] + text_position_x, text_position_y), text, fill="black", font=font)

        # Calculate the position to paste the image below the text, centered in the 80% image area
        x_offset = (thumbnail_size[0] - new_width) // 2
        y_offset = text_area_height + (image_area_height - new_height) // 2
        position_with_offset = (positions[i][0] + x_offset, positions[i][1] + y_offset)

        # Paste the scaled image onto the PDF canvas
        pdf_canvas.paste(img, position_with_offset)

    # Save the result as a PDF with the specified DPI
    pdf_canvas.save(pdf_path, resolution=dpi)


# Folder where .jpg images are stored
folder_path = 'C:\\Users\\ahg\\PycharmProjects\\ImagePDFCreation\\Images'

# Define the size of the PDF page in pixels for 8.5 x 11 inches at 300 DPI
dpi = 300  # Dots per inch
pdf_page_width, pdf_page_height = (int(8.5 * dpi), int(11 * dpi))


# Get all .jpg files in the folder
image_files = [f for f in os.listdir(folder_path) if f.endswith('.jpg')]

# Loop through the files in groups of 4
for i in range(0, len(image_files), 4):
    # Get the next 4 images (or fewer if at the end)
    image_set = image_files[i:i + 4]

    # Open the images
    images = [Image.open(os.path.join(folder_path, img)) for img in image_set]

    # Extract the filenames without the .jpg extension
    filenames = [os.path.splitext(img)[0] for img in image_set]

    # Create a name for the output PDF
    pdf_output_path = f'output_{i // 4 + 1}.pdf'

    # Create the PDF for the current set of images, with text
    create_pdf(images, filenames, pdf_output_path, pdf_page_width, pdf_page_height, dpi)

    print(f'Created PDF: {pdf_output_path}')
