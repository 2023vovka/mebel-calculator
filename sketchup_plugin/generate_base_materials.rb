require 'sketchup.rb'

module MebelMaterialsPlugin
  def self.create_materials
    model = Sketchup.active_model
    materials = model.materials
    
    # Хранилище базовых материалов и их цветов (RGB)
    base_materials = {
      "Ткань" => Sketchup::Color.new(138, 172, 200),    # Мягкий синий/серо-голубой
      "Поролон" => Sketchup::Color.new(220, 240, 120),  # Салатово-желтый
      "Фанера" => Sketchup::Color.new(222, 184, 135),   # Светло-коричневый (светлое дерево)
      "МДФ" => Sketchup::Color.new(160, 120, 90),       # Коричнево-серый
      "ДСП" => Sketchup::Color.new(245, 245, 220)       # Бежевый
    }

    # Начинаем транзакцию, чтобы все материалы создались как одно действие (удобно для отмены Ctrl+Z)
    model.start_operation('Создание базовых материалов мебели', true)

    created_count = 0
    updated_count = 0

    base_materials.each do |name, color|
      # Проверяем, существует ли уже материал с таким именем
      if materials[name]
        mat = materials[name]
        updated_count += 1
      else
        mat = materials.add(name)
        created_count += 1
      end
      # Назначаем цвет
      mat.color = color
    end

    model.commit_operation

    # Показываем сообщение пользователю
    UI.messagebox("Операция завершена!\n\nСоздано новых: #{created_count}\nОбновлено существующих: #{updated_count}\n\nТеперь вы можете найти их во вкладке Materials (Материалы) -> In Model (В модели).")
  end

  # Проверяем, загружался ли уже этот скрипт (чтобы не дублировать кнопку в меню при перезагрузке)
  unless file_loaded?(__FILE__)
    # Добавляем кнопку в меню Plugins (Extensions)
    menu = UI.menu('Plugins')
    menu.add_item('Создать базу материалов мебели') {
      self.create_materials
    }
    file_loaded(__FILE__)
  end
end
