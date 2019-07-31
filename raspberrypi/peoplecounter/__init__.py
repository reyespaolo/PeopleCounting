
#source /usr/local/bin/virtualenvwrapper.sh
import configparser
import time
import cv2


class PeopleCounting:

    def __init__(self, source=0, pi=False, show_window=True, width = 640, height = 480,font=cv2.FONT_HERSHEY_SIMPLEX, 
        entrance_counter=0, exit_counter=0, min_countour_area=600, binarization_threshold = 60, offset_trip_line = 50, reference_frame = None):
        self.__dict__.update(locals())

    def CheckEntranceLine(self, y, CoorYEntranceLine, CoorYExitLine):
        AbsDistance = abs(y - CoorYEntranceLine)	
        if ((AbsDistance <= 2) and (y < CoorYEntranceLine)):
            return 1
        else:
            return 0

    def CheckExitLine(self,y, CoorYEntranceLine, CoorYExitLine):
        AbsDistance = abs(y - CoorYExitLine)	
        if ((AbsDistance <= 2) and (y > CoorYExitLine)):
            return 1
        else:
            return 0


    def go_config(self, config_path=None):
        # load config
        config = configparser.ConfigParser()
        config.read(config_path)
        # platform
        self.pi = config.getboolean('platform', 'pi')
        self.show_window = config.get('platform', 'show_window')
        self.source = config.get('video_source', 'source')
        self.width = config.get('video_source', 'width')
        self.height = config.get('video_source', 'height')
        self.entrance_counter = int(config.get('pcm', 'entrance_counter'))
        self.exit_counter = int(config.get('pcm', 'exit_counter'))
        self.min_countour_area = int(config.get('pcm', 'min_countour_area'))
        self.binarization_threshold = int(config.get('pcm', 'binarization_threshold'))
        self.offset_trip_line = int(config.get('pcm', 'offset_trip_line'))
        self.run()

    def run(self):
        self.last_time = time.time()

        # opencv 3.x bug??
        cv2.ocl.setUseOpenCL(False)

        # STARTS HERE
        # connect to camera
        if self.pi:

            from picamera.array import PiRGBArray
            from picamera import PiCamera

            self.camera = PiCamera()
            self.camera.resolution = (int(self.width), int(self.height))


            self.camera.framerate = 20

            self.rawCapture = PiRGBArray(self.camera, size=(int(self.width), int(self.height)))

            time.sleep(1)  # let camera warm up

        else:
            self.camera = cv2.VideoCapture(self.source)
            # self.camera.resolution = (int(self.width), int(self.height))
            self.camera.set(3, 320)
            self.camera.set(4, 240)
            


        # feed in video
        if self.pi:

            for frame in self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True):

                image = frame.array
                self.process(image)
                self.rawCapture.truncate(0)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        else:

            while self.camera.isOpened():

                rval, frame = self.camera.read()
                self.process(frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break


    def process(self, frame):
        GrayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        GrayFrame = cv2.GaussianBlur(GrayFrame, (21, 21), 0)

        if self.reference_frame is None:
            self.reference_frame = GrayFrame

        FrameDelta = cv2.absdiff(self.reference_frame, GrayFrame)
        FrameThresh = cv2.threshold(FrameDelta, self.binarization_threshold, 255, cv2.THRESH_BINARY)[1]

        FrameThresh = cv2.dilate(FrameThresh, None, iterations=3)

        cnts,_= cv2.findContours(FrameThresh.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        QttyOfContours = 0

        CoorYEntranceLine = (float(self.height) / 2)-self.offset_trip_line
        CoorYExitLine = (float(self.height) / 2)+self.offset_trip_line
        cv2.line(frame, (0,int(CoorYEntranceLine)), (int(self.width),int(CoorYEntranceLine)), (0, 255, 0), 2)
        cv2.line(frame, (0,int(CoorYExitLine)), (int(self.width),int(CoorYExitLine)), (0, 255, 255), 2)

        for c in cnts:
            if cv2.contourArea(c) < self.min_countour_area:
                continue

            QttyOfContours = QttyOfContours+1    
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            CoordXCentroid = (x+x+w)/2
            CoordYCentroid = (y+y+h)/2
            ObjectCentroid = (int(CoordXCentroid),int(CoordYCentroid))
            cv2.circle(frame, ObjectCentroid, 1, (0, 0, 0), 5)
            if (self.CheckEntranceLine(CoordYCentroid,CoorYEntranceLine,CoorYExitLine)):
                self.entrance_counter += 1
            if (self.CheckExitLine(CoordYCentroid,CoorYEntranceLine,CoorYExitLine)):  
                self.exit_counter += 1

        cv2.putText(frame, "Entrance: {}".format(str(self.entrance_counter)), (10, 50),
                    self.font, 0.5, (0, 255, 0), 2)
        cv2.putText(frame, "Exit: {}".format(str(self.exit_counter)), (10, 70),
                    self.font, 0.5, (0, 255, 255), 2)
        if self.show_window:
            Frame = self.render_fps(frame)
            cv2.imshow("Original Frame", Frame)
            cv2.imshow("Dilate", FrameThresh)


    def render_fps(self, frame):
        this_time = time.time()
        diff = this_time - self.last_time
        fps = 1 / diff
        message = 'FPS: %d' % fps
        print(message)
        cv2.putText(frame, message, (10, int(self.height) - 20), self.font, 0.5, (255, 255, 255), 2)
        self.last_time = time.time()

        return frame