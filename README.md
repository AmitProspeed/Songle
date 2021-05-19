# SONGLE

Before running a file, do:

    pip3 install -r requirements.txt

To host app in GCP
 - gcloud config set project [PROJECT_NAME]
 - gcloud compute firewall-rules create allow-mongodb --allow tcp:27017
 - gcloud app deploy
 - Add App engine VM IP to the mongoDB network list
 - gcloud app browse
 - After use, disable app in App Engine, then delete Project to release resources

## Structure of data content fetched from spotify and stored in MongoDB

```
<song>
    <id> songID (an unique integer) </id>
    <title> What I've Done </title>
    <lyrics>
        In this farewell
        There's no blood, there's no alibi
        'Cause I've drawn regret
    </lyrics>
    <genre> Alternative/Indie, Hard rock </genre>
    <artist> Linkin Park </artist>
    <album> Minutes to Midnight </album>
    <year> 2007 </year>
</song>
```

## Screenshots

![Arch_Image](https://github.com/CUBigDataClass/IMMENSE_INFO_REPO/blob/main/images/se_1.png)

![Arch_Image](https://github.com/CUBigDataClass/IMMENSE_INFO_REPO/blob/main/images/se_2.png)

![Arch_Image](https://github.com/CUBigDataClass/IMMENSE_INFO_REPO/blob/main/images/se_3.png)

![Arch_Image](https://github.com/CUBigDataClass/IMMENSE_INFO_REPO/blob/main/images/se_4.png)
