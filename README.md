# Can I Park here?

This notebooks shows how you can use object detection for solving a simple problem like if you can park here.
I used [Custom Vision Object detection](https://customvision.ai/) to train my model.

![alt text](https://github.com/Azadehkhojandi/CanIParkhere/blob/master/Docs/Photos/CustomVision.JPG "customvision.ai screen capture")

![alt text](https://github.com/Azadehkhojandi/CanIParkhere/blob/master/Docs/Photos/ObjectDetection.JPG "jupyter screen capture")

![alt text](https://github.com/Azadehkhojandi/CanIParkhere/blob/master/Docs/Photos/Postman.JPG "postman screen capture")

## How to run

1- Create an Object detection project in [Custom Vision Object detection](https://customvision.ai/) - upload signs photos, tag your photos and train them 

2- You need to add settings.py file to your root folder and update the key values 

vision_subscription_key = ""
vision_base_url = "https://westus.api.cognitive.microsoft.com/vision/v2.0/"
customvision_prediction_key = ""
customvision_projectid=""
customvision_iterationid=""


## Resources
1. https://customvision.ai/
2. https://docs.microsoft.com/en-us/azure/cognitive-services/custom-vision-service/home
