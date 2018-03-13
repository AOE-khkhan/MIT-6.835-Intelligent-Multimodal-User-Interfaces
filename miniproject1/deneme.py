A = [0,9,178,222]
answer = []
def choose(i):
	import random
	x = random.randint(0,10)
	return x%2==0
merged = False

for i in range(0,len(A)-2,2):
	point1 = A[i]
	point2 = A[i+1]
	
	if choose(i):
		print "yee",i
		answer.append(A[i])
		answer.append(A[i+2])
		merged = True 
	else:
		answer.append(A[i])
		answer.append(A[i+1])
		answer.append(A[i+2])


print answer