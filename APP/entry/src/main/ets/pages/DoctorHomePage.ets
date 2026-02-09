import router from '@ohos.router';
import storage from '@ohos.data.storage'; // 导入storage模块
@Entry
@Component
struct DoctorHomePage {
  @State currentTime: string = this.getCurrentTime();
  @State lastUpdate: string = '2025-12-3 周三 12:01';

  // 写死的患者数据
  @State patients: Array<Patient> = [
    {
      id: '1',
      name: '王大爷',
      age: 78,
      lastUpdate: '2025/12/3 10:30',
      status: '健康',
      statusColor: '#4CAF50',
      bgColor: '#E8F5E8'
    },
    {
      id: '2',
      name: '李奶奶',
      age: 82,
      lastUpdate: '2025/12/3 09:15',
      status: '轻微认知障碍',
      statusColor: '#FF9800',
      bgColor: '#FFF3E0'
    },
    {
      id: '3',
      name: '张爷爷',
      age: 85,
      lastUpdate: '2025/12/3 11:45',
      status: '健康',
      statusColor: '#4CAF50',
      bgColor: '#E8F5E8'
    },
    {
      id: '4',
      name: '赵奶奶',
      age: 79,
      lastUpdate: '2025/12/3 08:20',
      status: '健康',
      statusColor: '#4CAF50',
      bgColor: '#E8F5E8'
    }
  ];



  build() {
    Column() {
      // ---------- 顶部标题栏 ----------
      Row() {
        // 返回按钮
        Image($r('app.media.back_arrow'))
          .width(24)
          .height(24)
          .onClick(() => {
            router.back();
          })

        Text('关爱·守护')
          .fontSize(20)
          .fontWeight(FontWeight.Bold)
          .fontColor(Color.White)
          .layoutWeight(1)
          .textAlign(TextAlign.Center)

        Text('医生')
          .fontSize(14)
          .fontColor(Color.White)
          .backgroundColor('#FF9800')
          .padding({ left: 8, right: 8, top: 4, bottom: 4 })
          .borderRadius(12)
      }
      .width('100%')
      .padding(16)
      .backgroundColor('#007DFF')

      // ---------- 时间区域 ----------
      Text(this.currentTime)
        .fontSize(16)
        .fontColor('#666666')
        .margin({ top: 16, bottom: 20 })


      //---------- 刷新数据 ----------
      Row() {
        Text('最新数据')
          .fontSize(16)
          .fontColor('#FFFFFF')

        Text('点击这里')
          .fontSize(16)
          .fontColor('#FFF2CC')
          .fontWeight(FontWeight.Bold)
          .margin({ left: 4 })
      }
      .width('55%')
      .height(48)
      .backgroundColor('#FF6B35')
      .borderRadius(24)
      .justifyContent(FlexAlign.Center)
      .margin({ bottom: 8 })
      .onClick(() => {
        this.refreshData();
      })

      Text(`上一次更新：${this.lastUpdate}`)
        .fontSize(12)
        .fontColor('#999999')
        .margin({ bottom: 20 })


      // ---------- 患者列表标题 ----------
      Row() {
        Text('患者列表')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
          .fontColor('#182431')
          .layoutWeight(1)

        Text(`共${this.patients.length}位患者`)
          .fontSize(14)
          .fontColor('#666666')
      }
      .width('100%')
      .padding({ left: 16, right: 16 })
      .margin({ bottom: 4 })




      // ---------- 患者列表 ----------
      Scroll() {
        Column() {
          ForEach(this.patients, (patient: Patient) => {
            this.buildPatientCard(patient)
          }, (patient: Patient) => patient.id)
        }
        .width('100%')
        .padding(16)
      }
      .layoutWeight(0)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }

  @Builder
  buildPatientCard(patient: Patient) {
    Column() {


      Row() {
        // 患者基本信息
        Column() {
          Text(patient.name)
            .fontSize(18)
            .fontWeight(FontWeight.Medium)
            .fontColor('#182431')
            .margin({ bottom: 4 })

          Text(`上次更新：${patient.lastUpdate}`)
            .fontSize(12)
            .fontColor('#999999')
        }
        .layoutWeight(1)

        // 年龄和状态
        Column() {
          Text(`${patient.age}岁`)
            .fontSize(14)
            .fontColor('#666666')
            .margin({ bottom: 8 })

          Text(patient.status)
            .fontSize(12)
            .fontColor(patient.statusColor)
            .backgroundColor(patient.bgColor)
            .padding({ left: 8, right: 8, top: 4, bottom: 4 })
            .borderRadius(4)
        }
        .alignItems(HorizontalAlign.End)
      }
      .width('100%')
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Color.White)
    .borderRadius(12)
    .margin({ bottom: 12 })
    .onClick(() => {
      this.viewPatientDetail(patient);
    })
  }

  // 查看患者详情
  private viewPatientDetail(patient: Patient): void {
    console.log('查看患者详情:', patient.name);
    // 跳转到患者详情页面
    router.pushUrl({
      url: 'pages/PatientDetailPage',
      params: { patientId: patient.id }
    });
  }

  // 获取当前时间
  private getCurrentTime(): string {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1;
    const date = now.getDate();
    const hour = now.getHours().toString().padStart(2, '0');
    const minute = now.getMinutes().toString().padStart(2, '0');
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    const weekday = weekdays[now.getDay()];

    return `${year}-${month}-${date} ${weekday} ${hour}:${minute}`;
  }
  // 刷新数据
  private refreshData(): void {
    const now = this.getCurrentTime(); // 获取当前时间
    this.lastUpdate = now; // 更新@State（页面显示）
    // 同步更新LocalStorage（持久化）
    this.lastUpdate = now; // @LocalStorageLink会自动同步到存储
  }
}

// 患者数据类型定义
interface Patient {
  id: string;
  name: string;
  age: number;
  lastUpdate: string;
  status: string;
  statusColor: string;
  bgColor: string;
}