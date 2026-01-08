def sumInt(x:int,y:int)->int:
    for i in range(10):
        x+=i
        print(f"x:{x}, i:{i} ;")
        
    print(x+y)
    return x+y


sumInt(10,100)