Reference Easy Import 安裝教學

用途：
這是一個讓動畫師在 Maya 中快速導入參考影片的工具，
能幫你一鍵建立控制器、鎖在相機上、播放影片、調整時間位移。
適合用來做角色動作、表情、實拍對位分析。

----

使用方法：

1) 把整個 Reference_easy_import 資料夾放進 Documents\maya\scripts\
2) 把Install.mel拖曳至Maya視圖
3) 會在Shelf/Custom直接出現小工具，點選即可使用

或是在步驟1後，在MAYA裡執行：

import Reference_easy_import; 
Reference_easy_import.run()

直接把上述這段，複製進Script Editor/ Python執行即可

----

備註:

Reload.py是備用檔案，重置Maya讀取該工具，可以忽略不管。

這個小工具是使用ChatGPT製作
目前測試過MAYA2020到2025都可以順利運行，
2020的話我個人是可以，但有朋友無法使用，
不過2022之後都是穩定運行的
若無法使用，請再告訴我~