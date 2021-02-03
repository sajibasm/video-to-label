# k means clustering to generate video summary
import sys
import imageio
import numpy as np
import cv2
import scipy.io

# k-means
from sklearn.cluster import KMeans

# System Arguments
# Argument 1: Location of the video
# Argument 2: Sampling rate (k where every kth frame is chosed)
# Argument 3: Percentage of frames in the keyframe summany (Hence the number of cluster)
# NOTE: pass the number of clusters as -1 to choose 1/50 the number of frames in original video
# Only valid for SumMe dataset

# optional arguments 
# Argument 4: 1: if 3D Histograms need to be generated and clustered, else 0
# Argument 5: 1: if want to save keyframes 
# Argument 6: 1: if want to save the frame indices
# Argument 7: directory where keyframes will be saved

# defines the number of bins for pixel values of each type {r,g,b}
num_bins=16

# size of values in each bin
range_per_bin=256/num_bins

#frame chosen every k frames
sampling_rate=int(sys.argv[2])

# number of centroids
percent=int(sys.argv[3])

# globalizing
num_centroids=0

# manual function to generate a 3D tensor representing histogram
# extremely slow
def generate_histogram(frame):
	print "Received frame"
	global num_bins, sampling_rate, num_centroids
	histogram=np.zeros((num_bins,num_bins,num_bins))
	for row in range(len(frame)):
		for col in range(len(frame[row])):
			r,g,b=frame[row][col]
			histogram[r/num_bins][g/num_bins][b/num_bins]+=1;
	return histogram
	print "Generated Histogram"

def save_keyframes(frame_indices, summary_frames):
	global sampling_rate, num_centroids
	if int(sys.argv[6])==1:
		print "Saving frame indices"
		out_file=open(sys.argv[7]+"frame_indices_"+str(num_centroids)+"_"+str(sampling_rate)+".txt",'w')
		for idx in frame_indices:
			out_file.write(str(idx*sampling_rate)+'\n')
		print "Saved indices"

	if int(sys.argv[5])==1:
		print "Saving frames"
		for i,frame in enumerate(summary_frames):
			cv2.imwrite(str(sys.argv[7])+"keyframes/frame%d.jpg"%i, frame)
		print "Frames saved"

def main():
	global num_bins, sampling_rate, percent, num_centroids
	print "Opening video!"
	video=imageio.get_reader(sys.argv[1]);
	print "Video opened\nChoosing frames"
	#choosing the subset of frames from which video summary will be generateed
	frames=[video.get_data(i*sampling_rate) for i in range(len(video)/sampling_rate)]
	print "Frames chosen"
	print "Length of video %d" % len(video)

	# converting percentage to actual number
	num_centroids=int(percent*len(video)/100)	
	if (len(video)/sampling_rate) < num_centroids:
		print "Samples too less to generate such a large summary"
		print "Changing to maximum possible centroids"
		num_centroids=len(video)/sampling_rate
		
	if len(sys.argv)>4 and int(sys.argv[4])==1:
		print "Generating 3D Tensor Histrograms"
		#manually generated histogram
		color_histogram=[generate_histogram(frame) for frame in frames]
		print "Color Histograms generated"

	#opencv: generates 3 histograms corresponding to each channel for each frame
	print "Generating linear Histrograms using OpenCV"
	channels=['b','g','r']
	hist=[]
	for frame in frames:
		feature_value=[cv2.calcHist([frame],[i],None,[num_bins],[0,256]) for i,col in enumerate(channels)]
		hist.append(np.asarray(feature_value).flatten())
	hist=np.asarray(hist)
	print "Done generating!"
	print "Shape of histogram: " + str(hist.shape)

	# clustering: defaults to using the histogram generated by OpenCV
	print "Clustering"

	# choose number of centroids for clustering from user required frames (specified in GT folder for each video)
	if percent==-1:
		video_address=sys.argv[1].split('/')
		gt_file=video_address[len(video_address)-1].split('.')[0]+'.mat'
		video_address[len(video_address)-1]=gt_file
		video_address[len(video_address)-2]='GT'
		gt_file='/'.join(video_address)
		num_frames=int(scipy.io.loadmat(gt_file).get('user_score').shape[0])
		# automatic summary sizing: summary assumed to be 1/100 of original video
		num_centroids=int(0.1*num_frames)

	kmeans=KMeans(n_clusters=num_centroids).fit(hist)
	print "Done Clustering!"

	print "Generating summary frames"
	summary_frames=[]

	# transforms into cluster-distance space (n_cluster dimensional)
	hist_transform=kmeans.transform(hist)
	frame_indices=[]
	for cluster in range(hist_transform.shape[1]):
		print "Frame number: %d" % (np.argmin(hist_transform.T[cluster])*sampling_rate)
		frame_indices.append(np.argmin(hist_transform.T[cluster]))
	
	# frames generated in sequence from original video
	frame_indices=sorted(frame_indices)
	summary_frames=[frames[i] for i in frame_indices]
	print "Generated summary"

	if len(sys.argv)>5 and (int(sys.argv[5])==1 or int(sys.argv[6])==1):
		save_keyframes(frame_indices, summary_frames)
		
if __name__ == '__main__':
	main()