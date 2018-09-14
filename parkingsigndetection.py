
import requests
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Rectangle
from PIL import Image
import io
import time
import numpy as np
from azure.cognitiveservices.vision.customvision.prediction import prediction_endpoint
from azure.cognitiveservices.vision.customvision.prediction.prediction_endpoint import models
get_ipython().run_line_magic('matplotlib', 'inline')



import settings
assert settings.vision_subscription_key 
assert settings.vision_base_url 
assert settings.customvision_prediction_key
assert settings.customvision_projectid
assert settings.customvision_iterationid



def recognizeText(image_data,mode='Handwritten'):
    
    
    text_recognition_url = settings.vision_base_url + "recognizeText"    

    headers = {'Ocp-Apim-Subscription-Key': settings.vision_subscription_key   ,
              'Content-Type':'application/octet-stream'}

    params  = {'mode': mode}

    response = requests.post(
        text_recognition_url, headers=headers, params=params, data=image_data)

    response.raise_for_status()

    # Extracting handwritten text requires two API calls: One call to submit the
    # image for processing, the other to retrieve the text found in the image.

    # Holds the URI used to retrieve the recognized text.
    operation_url = response.headers["Operation-Location"]

    # The recognized text isn't immediately available, so poll to wait for completion.
    analysis = {}
    poll = True
    while (poll):
        response_final = requests.get(
            response.headers["Operation-Location"], headers=headers)
        analysis = response_final.json()
        time.sleep(1)
        if ("recognitionResult" in analysis):
            poll= False 
        if ("status" in analysis and analysis['status'] == 'Failed'):
            poll= False

    
    return analysis




def ocr(image_data):

    ocr_url = settings.vision_base_url + "ocr"

   

    headers = {'Ocp-Apim-Subscription-Key': settings.vision_subscription_key,
               'Content-Type':'application/octet-stream'}
    params  = {'language': 'unk', 'detectOrientation': 'true'}
    
    response = requests.post(ocr_url, headers=headers, params=params, data=img_data)
    response.raise_for_status()

    analysis = response.json()

    return analysis



def findsigns(image_data,sign_recognizer):
    
    predictor = prediction_endpoint.PredictionEndpoint(settings.customvision_prediction_key)
    
    
    results = predictor.predict_image(settings.customvision_projectid, image_data, settings.customvision_iterationid)

    image = Image.open(io.BytesIO(image_data))
    np_image = np.array(image)

    signs =[]
    arrows=[]
    
    arrowadjustment=20
    
    # Display the results.
    for prediction in results.predictions:
        #print ("\t" + prediction.tag_name + ": {0:.2f}%".format(prediction.probability * 100), prediction.bounding_box.left, prediction.bounding_box.top, prediction.bounding_box.width, prediction.bounding_box.height)

        if (( prediction.tag_name == 'ParkingSign' and prediction.probability>0.3) or
            ('Arrow' in prediction.tag_name and prediction.probability>=0.05)): #

            h=np_image.shape[0]
            w=np_image.shape[1]
            x = int(prediction.bounding_box.left * w)
            y = int((prediction.bounding_box.top )* h)
            width = int(prediction.bounding_box.width * w)
            height = int(prediction.bounding_box.height * h)
            if(prediction.tag_name == 'ParkingSign'):
                signs.append({'probability':prediction.probability,'sign_coordinates':[x, y, x+width, y+height],'sign_size':[width,height]})
            if('Arrow' in prediction.tag_name):
                arrows.append({'probability':prediction.probability,'arrow':prediction.tag_name.replace('Arrow', ''),'arrow_coordinates':[x, y, x+width, y+height],'arrow_size':[width,height]})

            
    
    
    texts=[]
    
    if(sign_recognizer=='recognizeText'):
        analysis=recognizeText(image_data,'Printed')
        
        if ("recognitionResult" in analysis):
            # Extract the recognized text, with bounding boxes.
            polygons = [(line["boundingBox"], line["text"]) for line in analysis["recognitionResult"]["lines"]]

            #overlay the image with the extracted text
            for polygon in polygons:
                vertices = [(polygon[0][i], polygon[0][i+1]) for i in range(0, len(polygon[0]), 2)]
                text={"x":vertices[0][0],"y":vertices[0][1],"text":polygon[1],"boundingtype":"polygon","coordinates":vertices}
                texts.append(text)
               
  

    if(sign_recognizer=='ocr'):
        analysis=ocr(image_data)
        if ("regions" in analysis):
            # Extract the word bounding boxes and text.
            line_infos = [region["lines"] for region in analysis["regions"]]
            word_infos = []
            for line in line_infos:
                for word_metadata in line:
                    for word_info in word_metadata["words"]:
                        word_infos.append(word_info)


            for word in word_infos:
                bbox = [int(num) for num in word["boundingBox"].split(",")]
                text = word["text"]
                texts.append({"x":bbox[0],"y":bbox[1],"text":word["text"],"boundingtype":"rectangle","coordinates":[bbox[0],bbox[1],bbox[2],bbox[3]]})
               

            

    for sign in signs:
        
        sign_x1=sign['sign_coordinates'][0]
        sign_y1=sign['sign_coordinates'][1]
        sign_x2=sign['sign_coordinates'][2]
        sign_y2=sign['sign_coordinates'][3]
        sign_w=sign['sign_size'][0]
        sign_h=sign['sign_size'][1]
        
        sign["texts"]=[]
        for text in texts: 
            
            if(text["x"]>=sign_x1  and text["x"]<sign_x2 and text["y"]>=sign_y1 and text["y"]<sign_y2):
                sign["texts"].append(text)
           
        for arrow in arrows:
            
            arrow_x1=arrow['arrow_coordinates'][0]
            arrow_y1=arrow['arrow_coordinates'][1]
            arrow_x2=arrow['arrow_coordinates'][2]
            arrow_y2=arrow['arrow_coordinates'][3]
            arrow_w=arrow['arrow_size'][0]
            arrow_h=arrow['arrow_size'][1]
          
            if ((arrow_x1>=sign_x1 or abs(arrow_x1-sign_x1)<=arrowadjustment) and
                    (arrow_x2<=sign_x2 or abs(arrow_x2-sign_x2)<=arrowadjustment) and 
                    (arrow_y1>=sign_y1 or abs(arrow_y1-sign_y1)<=arrowadjustment) and 
                    (arrow_y2<=sign_y2 or abs(arrow_y2-sign_y2)<=arrowadjustment)) :
                    
                    if("arrow" in sign):
                        
                        if(sign["arrow"]["probability"]<arrow["probability"]):
                            sign["arrow"]= arrow
                    else:
                        sign["arrow"]= arrow
                    
            
    return signs
            



def displysigns(image_data,signs):
    
    
    plt.figure(figsize=(15, 15))

    image = Image.open(io.BytesIO(image_data))
    np_image = np.array(image)
    ax = plt.imshow(image, alpha=0.5)
    
    for sign in signs:

        sign_x1=sign['sign_coordinates'][0]
        sign_y1=sign['sign_coordinates'][1]
        sign_x2=sign['sign_coordinates'][2]
        sign_y2=sign['sign_coordinates'][3]
        sign_w=sign['sign_size'][0]
        sign_h=sign['sign_size'][1]
        patch_sign=Rectangle((sign_x1,sign_y1), sign_w, sign_h, fill=False, linewidth=2, color='r')
        ax.axes.add_patch(patch_sign)
        
        for text in sign["texts"]: 
            plt.text(text["x"], text["y"], text["text"], fontsize=10, weight="bold", va="center",ha="left")
            if(text["boundingtype"]=="rectangle"):
                patch  = Rectangle((text["coordinates"][0],text["coordinates"][1]), text["coordinates"][2], text["coordinates"][3], fill=False, linewidth=2, color='y')
                ax.axes.add_patch(patch)
            else:
                patch    = Polygon(text["coordinates"], closed=True, fill=False, linewidth=2, color='y')
                ax.axes.add_patch(patch)
               
                    
        if('arrow' in sign):
            arrow_x1=sign['arrow']['arrow_coordinates'][0]
            arrow_y1=sign['arrow']['arrow_coordinates'][1]
            arrow_x2=sign['arrow']['arrow_coordinates'][2]
            arrow_y2=sign['arrow']['arrow_coordinates'][3]
            arrow_w=sign['arrow']['arrow_size'][0]
            arrow_h=sign['arrow']['arrow_size'][1]
            patch_arrow=Rectangle((arrow_x1,arrow_y1), arrow_w, arrow_h, fill=False, linewidth=2, color='r')
            ax.axes.add_patch(patch_arrow)
        
        
            
         
    _ = plt.axis("off")
    plt.show()
