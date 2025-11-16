import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './index.css'

// Используем относительный путь для работы через прокси Vite
const API_URL = import.meta.env.VITE_API_URL || '/api'

// Компонент страницы "О проекте"
function AboutPage({ onBack }) {
  return (
    <div className="about-page">
      <button onClick={onBack} className="back-button">
        Назад
      </button>
      <p>
        Каждый из нас знает, как трудно составить идеальный план дня.
      </p>
      <p>
        С утра много энергии, после обеда хочется поспать, вечером появляются силы на творчество, но мы редко используем это правильно.
      </p>
      <p>
        Мы создали инструмент, который помогает размещать ваши дела в те часы, когда вы будете выполнять их максимально эффективно.
      </p>
      <p>
        Вы вводите список задач - мы думаем о планировании. Наш умный алгоритм распределяет дела по времени суток, в дальнейшем учитывая ваши предпочтения. Мы подстраиваемся под ваш личный ритм дня, чтобы сделать вашу жизнь проще и приятнее!
      </p>
      <p>
        Мы используем нейромодель, которая анализирует научные статьи, советы врачей и данные о продуктивности.
      </p>
      <p>
        Вы всегда видите, на какие источники опирается рекомендация, и можете оценивать их надёжность.
      </p>
      <p style={{ marginTop: '30px', fontStyle: 'italic' }}>
        "В потоке" - больше, чем список дел.
      </p>
    </div>
  )
}

function App() {
  const [currentPage, setCurrentPage] = useState('main') // 'main' или 'about'
  const [tasks, setTasks] = useState([])
  const [plan, setPlan] = useState(null)
  const [sources, setSources] = useState([])
  const [showSources, setShowSources] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [message, setMessage] = useState(null)

  // Рефы для звуков
  const addTaskSoundRef = useRef(null)
  const generatePlanSoundRef = useRef(null)

  // Форма добавления задачи
  const [taskForm, setTaskForm] = useState({
    title: '',
    category: '',
    mood: ''
  })

  const categories = ['Работа', 'Спорт', 'Отдых', 'Учеба', 'Встречи', 'Хобби', 'Другое']
  const moods = ['Позитивное', 'Нейтральное', 'Стрессовое', 'Творческое', 'Рутинное']

  // Загрузка задач при монтировании
  useEffect(() => {
    loadTasks()
  }, [])

  const loadTasks = async () => {
    try {
      const response = await axios.get(`${API_URL}/tasks`)
      setTasks(response.data)
    } catch (err) {
      console.error('Ошибка загрузки задач:', err)
    }
  }

  const playSound = (soundRef) => {
    if (soundRef.current) {
      soundRef.current.play().catch(err => {
        console.log('Ошибка воспроизведения звука:', err)
      })
    }
  }

  const handleAddTask = async (e) => {
    e.preventDefault()
    if (!taskForm.title || !taskForm.category || !taskForm.mood) {
      setError('Заполните все поля')
      return
    }

    try {
      await axios.post(`${API_URL}/tasks`, taskForm)
      setTaskForm({ title: '', category: '', mood: '' })
      setError(null)
      setMessage('Задача добавлена!')
      setTimeout(() => setMessage(null), 3000)
      loadTasks()
      // Воспроизводим звук
      playSound(addTaskSoundRef)
    } catch (err) {
      setError('Ошибка добавления задачи: ' + err.message)
    }
  }

  const handleDeleteTask = async (taskId) => {
    try {
      await axios.delete(`${API_URL}/tasks/${taskId}`)
      setMessage('Задача удалена!')
      setTimeout(() => setMessage(null), 3000)
      loadTasks()
    } catch (err) {
      setError('Ошибка удаления задачи: ' + err.message)
    }
  }

  const handleGeneratePlan = async () => {
    if (tasks.length === 0) {
      setError('Добавьте хотя бы одну задачу')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const response = await axios.post(`${API_URL}/plan/generate`, {
        tasks: []
      })
      setPlan(response.data)
      setSources(response.data.sources || [])
      setMessage('План успешно сгенерирован!')
      setTimeout(() => setMessage(null), 3000)
      // Воспроизводим звук
      playSound(generatePlanSoundRef)
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message
      setError('Ошибка генерации плана: ' + errorMsg)
      console.error('Ошибка генерации плана:', err.response?.data)
    } finally {
      setLoading(false)
    }
  }

  const handleRegeneratePlan = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.post(`${API_URL}/plan/regenerate`)
      setPlan(response.data)
      setSources(response.data.sources || [])
      setMessage('План перегенерирован!')
      setTimeout(() => setMessage(null), 3000)
    } catch (err) {
      setError('Ошибка перегенерации плана: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateTaskTime = async (taskId, newTimeBlock) => {
    try {
      await axios.put(`${API_URL}/plan/update`, {
        task_id: taskId,
        new_time_block: newTimeBlock
      })
      setMessage('План обновлен!')
      setTimeout(() => setMessage(null), 3000)
      handleRegeneratePlan()
    } catch (err) {
      setError('Ошибка обновления плана: ' + err.message)
    }
  }

  const handleMarkSourceUntrusted = async (sourceId) => {
    try {
      await axios.post(`${API_URL}/sources/${sourceId}/untrust`)
      setMessage('Источник помечен как недоверенный')
      setTimeout(() => setMessage(null), 3000)
    } catch (err) {
      setError('Ошибка: ' + err.message)
    }
  }

  const loadSources = async () => {
    try {
      const response = await axios.get(`${API_URL}/sources`)
      setSources(response.data)
      setShowSources(true)
    } catch (err) {
      setError('Ошибка загрузки источников: ' + err.message)
    }
  }

  const handleCalendarSync = () => {
    // Пока ничего не делает
    setMessage('Синхронизация с календарем будет доступна в будущих обновлениях')
    setTimeout(() => setMessage(null), 3000)
  }

  if (currentPage === 'about') {
    return (
      <div className="container">
        <AboutPage onBack={() => setCurrentPage('main')} />
      </div>
    )
  }

  return (
    <div className="container">
      {/* Скрытые аудио элементы для звуков */}
      <audio ref={addTaskSoundRef} src="/sounds/add-task.mp3" preload="auto" />
      <audio ref={generatePlanSoundRef} src="/sounds/generate-plan.mp3" preload="auto" />

      {/* Кнопки в шапке */}
      <div className="header-buttons">
        <button className="header-button" onClick={() => setCurrentPage('about')}>
          О проекте
        </button>
        <button className="header-button" onClick={handleCalendarSync}>
          Синхронизация с календарем
        </button>
      </div>

      <h1>Какие планы?</h1>

      {message && <div className="success">{message}</div>}
      {error && <div className="error">{error}</div>}

      {/* Форма добавления задачи */}
      <section>
        <div className="form-container">
          <form onSubmit={handleAddTask}>
            <div className="form-group">
              <label>Название задачи</label>
              <input
                type="text"
                value={taskForm.title}
                onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })}
                placeholder="Например: Встреча с командой"
              />
            </div>
            <div className="form-group">
              <label>Категория</label>
              <select
                value={taskForm.category}
                onChange={(e) => setTaskForm({ ...taskForm, category: e.target.value })}
              >
                <option value="">Выберите категорию</option>
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Эмоциональный окрас</label>
              <select
                value={taskForm.mood}
                onChange={(e) => setTaskForm({ ...taskForm, mood: e.target.value })}
              >
                <option value="">Выберите окрас</option>
                {moods.map(mood => (
                  <option key={mood} value={mood}>{mood}</option>
                ))}
              </select>
            </div>
            <button type="submit" className="oval">Добавить задачу</button>
          </form>
        </div>
        <button 
          onClick={handleGeneratePlan} 
          disabled={loading || tasks.length === 0}
          className="large"
        >
          {loading ? 'Генерация...' : 'Сгенерировать план'}
        </button>
      </section>

      {/* Список задач */}
      {tasks.length > 0 && (
        <section>
          <h2>Ваши задачи ({tasks.length})</h2>
          <ul className="task-list">
            {tasks.map(task => (
              <li key={task.id} className="task-item">
                <div className="task-info">
                  <div className="task-title">{task.title}</div>
                  <div className="task-meta">
                    {task.category} • {task.mood}
                  </div>
                </div>
                <button
                  onClick={() => handleDeleteTask(task.id)}
                  className="danger"
                  style={{ fontSize: '14px', padding: '8px 12px', minWidth: '40px' }}
                  title="Удалить задачу"
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Кнопки управления */}
      {plan && (
        <div className="buttons-group">
          <button onClick={handleRegeneratePlan} disabled={loading} className="secondary">
            Перегенерировать план
          </button>
          <button onClick={loadSources} className="secondary">
            Источники
          </button>
        </div>
      )}

      {/* План на день */}
      {plan && (
        <section className="plan-section">
          <h2>Ваш план на день</h2>

          {plan.morning && plan.morning.length > 0 && (
            <div className="time-block morning">
              <h3>Утро</h3>
              {plan.morning.map((item, idx) => (
                <div key={idx} className="plan-item">
                  <div className="plan-item-title">{item.task_title}</div>
                  <div className="task-meta">{item.task_category} • {item.task_mood}</div>
                  <div className="plan-item-justification">{item.justification}</div>
                  <button
                    onClick={() => handleUpdateTaskTime(item.task_id, 'день')}
                    className="secondary"
                    style={{ marginTop: '10px', fontSize: '12px' }}
                  >
                    Переместить в день
                  </button>
                  <button
                    onClick={() => handleUpdateTaskTime(item.task_id, 'вечер')}
                    className="secondary"
                    style={{ marginTop: '10px', fontSize: '12px', marginLeft: '5px' }}
                  >
                    Переместить в вечер
                  </button>
                </div>
              ))}
            </div>
          )}

          {plan.day && plan.day.length > 0 && (
            <div className="time-block day">
              <h3>День</h3>
              {plan.day.map((item, idx) => (
                <div key={idx} className="plan-item">
                  <div className="plan-item-title">{item.task_title}</div>
                  <div className="task-meta">{item.task_category} • {item.task_mood}</div>
                  <div className="plan-item-justification">{item.justification}</div>
                  <button
                    onClick={() => handleUpdateTaskTime(item.task_id, 'утро')}
                    className="secondary"
                    style={{ marginTop: '10px', fontSize: '12px' }}
                  >
                    Переместить в утро
                  </button>
                  <button
                    onClick={() => handleUpdateTaskTime(item.task_id, 'вечер')}
                    className="secondary"
                    style={{ marginTop: '10px', fontSize: '12px', marginLeft: '5px' }}
                  >
                    Переместить в вечер
                  </button>
                </div>
              ))}
            </div>
          )}

          {plan.evening && plan.evening.length > 0 && (
            <div className="time-block evening">
              <h3>Вечер</h3>
              {plan.evening.map((item, idx) => (
                <div key={idx} className="plan-item">
                  <div className="plan-item-title">{item.task_title}</div>
                  <div className="task-meta">{item.task_category} • {item.task_mood}</div>
                  <div className="plan-item-justification">{item.justification}</div>
                  <button
                    onClick={() => handleUpdateTaskTime(item.task_id, 'утро')}
                    className="secondary"
                    style={{ marginTop: '10px', fontSize: '12px' }}
                  >
                    Переместить в утро
                  </button>
                  <button
                    onClick={() => handleUpdateTaskTime(item.task_id, 'день')}
                    className="secondary"
                    style={{ marginTop: '10px', fontSize: '12px', marginLeft: '5px' }}
                  >
                    Переместить в день
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Источники */}
      {showSources && sources.length > 0 && (
        <section className="sources-section">
          <h2>Источники информации</h2>
          {sources.map(source => (
            <div key={source.id} className="source-item">
              <div>
                <div style={{ fontWeight: 600, marginBottom: '5px' }}>{source.title}</div>
                <a href={source.link} target="_blank" rel="noopener noreferrer" className="source-link">
                  {source.link}
                </a>
              </div>
              <button
                onClick={() => handleMarkSourceUntrusted(source.id)}
                className="danger"
                style={{ fontSize: '12px' }}
              >
                Не доверять источнику
              </button>
            </div>
          ))}
        </section>
      )}
    </div>
  )
}

export default App
