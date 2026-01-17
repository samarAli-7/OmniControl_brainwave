from ultralytics import YOLO


model = YOLO("yolo26n-pose.pt") 


model.train(
    data="hand-keypoints.yaml", 
    epochs=50, 
    imgsz=320,      
    batch=16,       
    workers=0,      
    mosaic=0.0,     
    val=False,      
    amp=True,       
    device=0,        
    name="hand_model" )